# RUNPLANS.md: session 3, S3T-3 (M3)

Paper only. **Nothing here runs before the Overseer's LOAD GO.** Repo root = `<workspace>`, and every command runs from there.

## 0. What is staged (all under `build/agent3/`, nothing running)

| file | what | state |
|---|---|---|
| `session3/queue-s3.jsonl` | 9 rows: s4bN16 (READY-N.md option C), s4bQ5, f10a3, f10b3, s4b07r, s4bV0, s4bLV, f10aL, f10bL | Append to `s4b/queue.jsonl` at LOAD GO. JSON parses, and no id clashes with `queue-state.jsonl`. |
| `s4b/s4b_check.py` | new ids get the proofs of the row they repeat. s4bLV→w6gA (G5: 0 K, 0 F), s4b07r→s4b07, s4bQ5→s4b18 at `quantum 500 us`, f10a3/f10aL→f10a, f10b3/f10bL→f10b, plus a new **s4bV0** branch | Edited and tested on old runs (§6). |
| `s4b/postcheck.ps1` | cases for the new ids (bases and allow-new below), P2c on s4bLV and f10b3/f10bL, and the new `F10` step (f10_rule) on the L-route rows | Edited. It parses, and the regex routing was tested. Not running. |
| `session3/f10_rule.py` | the strict finding-10 rule (SESSION2 L3128-3132). s4b_check only tests the owner lr range. | Tested on 9 old runs (§6). |
| `session3/cpuload.ps1` | controlled load: N busy children, each ends itself. It kills only its own pids, checked by pid + start time. | Parse-checked only, **never run**. |
| `session3/KILL-AUDIT.md` | harness kill-path audit (E2.1) | SAFE-IF, see §5 |

New gate markers. M3 creates them only after LOAD GO:
- `session3/go-user`: q500 allowed.
- `session3/go-quiet`: quiet host confirmed.
- `session3/go-load`: cpuload started.
- `session3/go-n`: the ready-N measurement row s4bN16 allowed (s4b25's args at split 16; checked as row 11 against RT).

The old `ready-later` / `ready-quiet` / `ready-v0` markers are not used, and `ready-s4b-off` (present) is still required.

## 1. Host classes

| row | host | why | game time |
|---|---|---|---|
| (c) s4bQ5 | **OK under user load** | Functional proof only (init line, sleep_fail = 0). Sleep failures don't depend on load. | 265 s est, cap 420 |
| (d1) f10a3, f10b3 | **QUIET**: no build, **no Minecraft**, no other game | The whole point is "quiet host, no hang" (p = 0.03 if both are clean) | 2 × 560 est, cap 600 |
| (b) s4b07r + s4bV0 | **QUIET**, back to back | Row 7's F 92 ran under the -j8 build. The pair must share one host state to be comparable. | 2 × 560, cap 600 |
| (a) s4bLV | **QUIET** | Verify mode runs at ~10-17 fps, and load made the w6gA hang. A loaded FAIL would be unreadable. | 1860 est, cap 1800 |
| (d2/d3) f10aL, f10bL | **CONTROLLED LOAD**: quiet host + `cpuload.ps1 -Threads 8`, no build, **no Minecraft** | Minecraft ≠ a controlled load. The load must be known and repeatable. It also keeps the PC at ~100 % for ~22 min. | 2 × 560, cap 600 |

Every row except s4bQ5 needs the user's Minecraft **closed by the user**. We never close it. While the user plays, only s4bQ5 can run, and even that competes with the game for CPU and GPU for ~5 min. The Overseer decides.

## 2. Procedure at LOAD GO (M3 runs it, one background command per process)

**Pre-flight** (read-only):
```powershell
Get-Process legodimensions, clang*, cl, ninja, link, lld-link -ErrorAction SilentlyContinue   # expect nothing
Get-Process Minecraft*, javaw -ErrorAction SilentlyContinue | Select-Object Name, Id           # quiet/load sessions: expect nothing (never touch it)
Test-Path perf-notes\WINDOW-HOLD.txt                                                           # expect False
python -B build\agent3\s4b\bincheck.py build\agent2\devoff4b-bin --set off                    # exit 0 (exe 170,350,080 B, 11-22 20:48)
```
Then:
1. Append the needed rows of `session3/queue-s3.jsonl` to `s4b/queue.jsonl`, all 8 or only the approved ones.
2. Create the go-markers for the approved sessions: `New-Item build\agent3\session3\go-quiet -ItemType File`, and the same for go-user. Delete `build\agent3\s4b\STOP`.
3. Start the three background processes. `-Until` / `-LastLaunch` / `-GamesClosed` are times **today** (the scripts do `Today + time`, so a window can't cross midnight):
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\s4b\hostload.ps1  -Until HH:mm:ss        # f10 rows need hostload.csv
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\s4b\postcheck.ps1 -Until HH:mm:ss
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\s4b\s4b-queue.ps1 -LastLaunch HH:mm -GamesClosed HH:mm -QuietCpuPct 40 -QuietSampleSec 10
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\s4b\wait-event.ps1 -Minutes 20 -Reset    # wakes M3 on DONE/SKIP/checked
```
4. **Session L** (controlled load) runs only after session Q's rows are DONE. Stop the queue with the STOP file, then: `cpuload.ps1 -Threads 8 -Minutes 25`, wait 30 s, create `go-load`, delete STOP, and restart the queue with **`-QuietCpuPct 100`**. The 40 % gate would otherwise block on our own load. Build processes and check scripts still block it.
5. At the end: create `s4b\STOP` and delete the go-markers. hostload and postcheck stop at `-Until`. If cpuload is still up, stop it with the `session3\cpuload.STOP` file.

Caveats:
- A row whose `est` would end after `-GamesClosed` is recorded as **skipped**, and skipped ids count as done (no re-run). Set GamesClosed ≥ start + session total + 15 min.
- The queue waits while any `legodimensions` process exists, while an Agent 8 runner is active (guard.ps1), and while a check script runs.
- Don't type other runner script names in shell commands while the queue can launch (guard.ps1 matches command lines).

## 3. The rows

### (a) s4bLV: p2fc + verify, cap 1800 s (RESUME §6 item 2; S21 A, b2r L1065)
- **Command (queue row):** `run-game.ps1 -BinDir build\agent2\devoff4b-bin -Seconds 1800 -Tag s4b-LV-p2fcv-level-long -InputScript build\agent3\toypad\routes\level-l.txt -Cvar "framerate_limit=0;shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true;physical_protect_keep_watch=true;physical_protect_keep_watch_verify=true;slow_frame_log_ms=1"`, with the toypad sidecar (`toypad: true`).
- **Checkers** (postcheck runs them):
  - `s4b_check.py --row s4bLV --cand <run> --base <s4bL0 run> --allow-new "C1 keep-watch|C1 verify|slow frame|memexport full-buffer"`
  - `p2c_check.py <run>`
  - `f10_rule.py <run>`
- **Pass, all of these:**
  - exit 0 and no crash (a hang dump is allowed only under the f10 WARN case).
  - Tags 3/3 LOAD lines, and the L route reaches the level: mark `vortex`, ideally `end`.
  - s4b_check proofs: init "C1 keep-watch: on" ×1, first kept ≥ 1, "C1 verify: on" ≥ 1, **K = 0 and F = 0 (G5)**, kept count rises, gate D lines 0, G8 lines 0, cvars = w6gA's set, P2 counter total = 0, and 0 BASE misses beyond the allowed families.
  - p2c RESULT PASS.
  - f10_rule PASS, or WARN (the only STUCK-LOCK is finding 10 and the run still reaches the level).
- **Inconclusive, not FAIL:** `vortex` not reached by 1800 s with no error. s4b07 reached story-load at 202 s (step 104 of 119) in 600 s, and w6gA was still at story-load at 600 s. Report it with the last mark.
- **FAIL:** K > 0, F > 0, any non-finding-10 STUCK-LOCK, a crash, P2 total > 0. Any of these blocks C1 default-ON. Report to the Overseer.
- **Time:** ≈ 31 min of game + ~2 min of checks.

### (b) s4bV0: C1 OFF + verify (Agent 12 predicts F > 0), paired with s4b07r
- **s4b07r** = row 7 exactly, `-Cvar "physical_protect_hold_global_lock=true;physical_protect_keep_watch=true;physical_protect_keep_watch_verify=true"`.
- **s4bV0** = the same with `physical_protect_keep_watch=false`.
- Both: devoff4b-bin, L route + toypad, `-Seconds 600`, quiet host, back to back.
- **Checkers:**
  - `s4b_check.py --row s4b07r|s4bV0 --base <s4bL0 run> --allow-new "C1 keep-watch|C1 verify"`
  - `f10_rule.py`
  - The F comparison over the same window:
```powershell
foreach ($r in '<s4b07r run>','<s4bV0 run>') { (Select-String -Path "build\agent3\runs\$r\game*.log" -Pattern 'C1 verify F:').Count }
```
  - Then compare per mark window: take the input.csv marks reached by both runs (`cmd=mark`), and the log stamps against `run.json started_epoch_s`.
- **Read-out:**
  - **s4b07r:** K = 0 is required (gate A; K > 0 = FAIL, report).
  - **s4bV0:** "C1 verify: on" must appear. Without it, F = 0 proves nothing → INCONCLUSIVE. keep-watch must be off (the new s4bV0 branch checks init-on / first kept / kept = 0).
  - **V0 F > 0** → Agent 12's prediction holds: F is not caused by keep-watch.
  - **V0 F = 0 with 07r F > 0** → it is refuted: F comes with keep-watch.
  - **Both 0** → row 7's F 92 was tied to the build load. Inconclusive for the race; report.
- **Time:** ≈ 2 × 10 min + checks ≈ 22 min.

### (c) s4bQ5: GPU wait back-off at Q = 500 µs, stats on (RESUME §6 item 1; agent9 HANDOFF L151-154)
- **Command:** `run-game.ps1 -BinDir build\agent2\devoff4b-bin -Seconds 420 -Tag s4b-Q5-gw-q500 -InputScript harness\routes\b-gate-menus-long.txt -Env "LEGO_GPU_WAIT_BACKOFF_US=500;LEGO_GPU_WAIT_STATS=1"`. Spin stays at its default of 30 µs. This is s4b18 with Q = 500 instead of 250.
- **Checkers:**
  - `s4b_check.py --row s4bQ5 --cand <run> --base <s4b01 run> --allow-new "GPU wait"`
  - `python -B build\agent3\s4b\gw_stats.py <run>` (manual, parses the fields by name)
- **Pass:**
  - Exactly one "GPU wait back-off: ON (quantum 500 us, spin 30 us); stats ON; GetData hook built." line.
  - Every stats line parsed, and **sleep_fail = 0 in all of them** (max = 0).
  - No STUCK-LOCK, exit 0, no dumps, 0 BASE misses beyond "GPU wait".
- **Host:** fine under user load. **Time:** ≈ 5 min + 1 min of checks.

### (d) finding-10 follow-ups (f10/RESULTS.md "Possible next steps")
- **d1, third quiet pair, f10a3 + f10b3.** Same args as f10a/f10b, plus `-GpuLog` (NVML clocks, for the laptop power-budget question):
  - f10a3: `shared_memory_upload_nontemporal_copy=true;slow_frame_log_ms=1`
  - f10b3: `framerate_limit=0;shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true;physical_protect_keep_watch=true;physical_protect_keep_watch_verify=false;slow_frame_log_ms=1`
  - Both: devoff4b-bin, L route + toypad, 600 s, quiet gate `-QuietCpuPct 40 -QuietSampleSec 10`.
- **d2, controlled-load repeat, f10aL + f10bL.** The same cvars under `cpuload.ps1 -Threads 8` (8 busy user-mode processes on 12 logical CPUs, no build), queue at `-QuietCpuPct 100`.
- **d3, loaded M1 row with slow_frame_log_ms=1.** f10aL is exactly this: s4b20's M1 set + slow_frame_log_ms=1 under load. One run covers d2 and d3.
- **Checkers:**
  - `s4b_check.py --row <id> --base <s4bL0 run> --allow-new "slow frame|memexport full-buffer"`, with `C1 keep-watch|` in front for the b rows. Proofs: cvars as planned, tags 3/3, reached level, quiet host = 0 build rows, G8 lines 0, STUCK-LOCK count.
  - `p2c_check.py` on f10b3 and f10bL.
  - `f10_rule.py` on all four.
  - Afterwards, the f10 tables: copy `build\agent3\f10\run_n2.ps1` to an n = 3 version that adds the new run dirs (paper, BelowNormal).
- **Pass (functional):** exit 0, tags 3/3, `vortex` reached, f10_rule PASS or WARN.
- **Science read-out:**
  - d1 with no hang in either run → quiet 0/6 vs loaded 4/6 → one-sided Fisher p = 0.03.
  - d2 hang(s) that match finding 10 → load is the trigger, shown directly.
  - d3: does M1's 12 s frame show memexport syncs in its slow-frame line?
- **Time:** d1 ≈ 20 min, d2+d3 ≈ 22 min, cpuload running 25 min.

## 4. Sessions and totals

| session | rows (order) | needs | ≈ wall time |
|---|---|---|---|
| U | s4bQ5 | go-user (OK under user load) | 7 min |
| N | s4bN16 (READY-N.md option C; uncapped title, so a quiet host is preferred) | go-n | 5 min |
| Q1 | f10a3, f10b3, s4b07r, s4bV0 | go-quiet; no Minecraft, no build | 45 min |
| Q2 | s4bLV | go-quiet | 34 min |
| L | f10aL, f10bL | cpuload + go-load; no Minecraft, no build | 25 min |

All five ≈ 1 h 55 min of machine time. Q1, Q2 and L can be split across separate quiet periods. U can run any time. N should run before the `ready-N` decision.

## 5. Kill safety (KILL-AUDIT.md, E2.1, sha256 5427F71E; key sites re-read by M3)
- **Normal close.** run-game.ps1 L302-304 sends WM_CLOSE to its own `$gamePid` windows, then calls `$p.Kill()` on **its own** Process object.
- **The queue.** s4b-queue.ps1 kills only the `-PassThru` children it started (L196, 241, 246-250).
- **Ruled out.** No taskkill, wmic, Stop-Process by name, or psutil. No Minecraft name anywhere in the harness.
- **cpuload.ps1.** Kills only the pids it started, re-checked by StartTime. Each child also exits on its own after -Minutes.
- **R1, holdwatch-m.ps1 L36-41.** Walks the process tree by ParentProcessId with no creation-time check (theoretical pid reuse). It fires only for `matrix` rows when `perf-notes/WINDOW-HOLD.txt` appears. **None of these 8 rows is a matrix row**, and we write no HOLD files.
- **R2, holdwatch.ps1 L25-38.** Picks the first `legodimensions` under `build\agent3\runs` started ≥ NotBefore-2 s. It can only ever hit a game, and only on a HOLD file. Another agent's concurrent game isn't possible, because run-game refuses when any legodimensions process exists.
- **Verdict: safe for these rows.** No path can touch Minecraft or any process that isn't ours.

## 6. Dry tests done (paper, BelowNormal, on existing runs)
- **f10_rule.py:**
  - s4b20 and w6gB → **WARN**: 1 event each, cs 84959EDC, owner 0x17 lr 83FAF200, waiter 82A2A270, recovered, level reached. This matches RESULTS.md.
  - w6gA → FAIL: the event is finding 10, but the run didn't reach the level in 600 s.
  - s4b24 → FAIL by default, WARN with `--no-level` (a menu route).
  - f10a, f10b, f10a2, f10b2 → PASS (0 events).
- **s4b_check.py after the edit:**
  - s4b18 → unchanged (PASS?, 0 misses).
  - s4bQ5 on the s4b18 run → correct MISS ("quantum 500 us" is absent).
  - s4bLV on the w6gA run → all 14 w6gA proofs.
  - s4bV0 on the s4b07 run → correct MISS (keep-watch was on), F 92 reported.
  - f10a3 on the f10a2 run → PASS?.
