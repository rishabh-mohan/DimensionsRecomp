# W6: proof-and-gates table and read-out steps (v2)

Agent 12, task #11 (run 2), 2026-11-22 ~20:20. This is v2 of the 17:05 table (task #32). It adds:
- **G11 (power overlay)** and **G12 (quiet gate: strict or relaxed)**, as Agent 1 asked at 19:31;
- the corrections from two read-only checks: the counter script against the s4-p2c source, and this table's facts
  against the diffs, b2r and S4-DRAFT;
- **run_gates (task #15, 21:55):** every gate G1-G12 on a finished matrix in one command, one table and the RECORD
  line (Tools). Nothing in it is tied to W6, so it serves W7-W10 unchanged.

It is written for Agent 5's W6 draft (`build/agent5/w6-draft/README.md` and `matrix-w6.json`, both 14:19). Agent 5
merges what it takes; Agent 8 owns the read-out and W6's promotion. **No W6 run has happened.** Both tools are tested
on existing logs (Tools, below), and so is run_gates, which runs every gate.

## Arms (from matrix-w6.json, unchanged)

| arm | switches | cvars beyond `framerate_limit=0` |
|---|---|---|
| s0 (ref) | none | every S4b switch at its default OFF |
| p2 | #8 P2 | `shared_memory_single_hold_rearm=true` |
| p2f | #8 + #5 fix (i) | p2's + `physical_protect_hold_global_lock=true` |
| p2fc | #8 + #5 + #4 C1 v3 | p2f's + `physical_protect_keep_watch=true`, `physical_protect_keep_watch_verify=false` |

- **Timed:** `run\run-matrix.ps1 -Matrix <matrix> -Only s0,p2,p2f,p2fc -Repeats 3 -ColdShared -NoPrompt`. That is 1
  shared cold run + 12 = 13 runs, ~33 min. It runs only on the user's desktop, never as an agent run.
- **Keep `"sys_csv": true`** (matrix-w6.json L14). G11 is read from it.
- **Night plan** (why the deadlines matter):
  - G2-G5 and G8's untimed runs happen in Agent 3's S4b queue. Agent 2's bins come ~20:30; the queue runs to ~22:50.
  - Anything the user must do is ready by 23:30.
  - The user double-clicks `bench/agent5/launch/RUN-NIGHT.cmd` at ~23:45.
  - W6 runs only after Agent 3's queue passes and Agent 8 promotes W6. Timed runs start by 06:45 and end before 07:30.

**Untimed runs** (agent runs on the S4b bin, not in the matrix):

| run | cvars beyond `framerate_limit=0` | route | feeds |
|---|---|---|---|
| side 1 | p2f's + `shared_memory_upload_hash_log=true`, `slow_frame_log_ms=1` | title, no input, ≥ 220 s | G4, R5 |
| side 2 | p2fc's + `shared_memory_upload_hash_log=true`, `slow_frame_log_ms=1` | title, no input, ≥ 220 s | G4, G8, R4, R5 |
| gate A | p2fc's, but `physical_protect_keep_watch_verify=true`; + `slow_frame_log_ms=1` | title, Agent 3's menu walk, one level load (Toy Pad = yes, 17:27) | G4, G5, G8 |
| side 3 (suggested) | p2fc's + `slow_frame_log_ms=1` | `harness/routes/attract-long.txt` (~472 s; the 3D attract scene, no figures) | G4 coverage |

- **Gate A** with p2fc's set (P2 ON too) also covers the whole timed stack over a level load.
- **Side 3** goes where the memexport activity is. On S4a, the attract route showed activity in 3626 of 28704
  slow-frame lines; the title showed it in 5 of 74714 (G4 below). Agent 3 ran this route on S4a
  (`build/agent3/runs/20261122-140637-s4a-udiag-attract`).
- `slow_frame_log_ms=1` adds the counter and costs nothing in an untimed run.

## Tools

### P2 counter check (G4, R6)

```
python build\agent12\p2c-check\p2c_check.py <run dir | log files, oldest first> [--json OUT] [--bin PATH]
```

- **Logs read:** `game.N.log` ... `game.1.log`, then `game.log`, oldest first. spdlog rotates at 5 MB × 20 files, and
  a relaunch appends to `game.log`.
- **Processes:** a new process starts at `Startup: launching the module`, a frame-index restart, or a fall in T.
- **Per process:** T, the F on logged lines, the first frame with T > 0, the last counter line, and how long the log
  goes on after it. Also the memexport activity sums.

| RESULT (last line) | exit | meaning |
|---|---|---|
| `PASS (total 0)` | 0 | the fallback never ran, up to the last logged frame |
| `FAIL (total N)` | 1 | it ran: P2 ON waits for Agent 1's cap decision (b2r §22) |
| `NO DATA` | 3 | no slow-frame lines; lines without the field (no s4-p2c); or no log |
| `PARTIAL` | 3 | T = 0, but some process has no counter lines, or lines with and without the field |
| `ERROR` | 4 | the script failed: send the run dir to Agent 12 |
| (usage) | 2 | |

- **Only PASS is a pass.**
- **WARNs:** the log goes on > 5 s after a process's last counter line; the last slow-frame line is cut off at exit;
  more than one process (their totals are added); T falls with no restart; T rises by less than the frame's F.
- **`--bin PATH`** checks the bin's .exe/.dll files, subfolders too. It says `(this build has s4-p2c)` when they contain
  the field's format string.
- **Source check:** a read-only subagent agreed on 10 of 10 points.
  - The format is REXGPU_INFO at o1-v3/o2-v3 `src/graphics/d3d12/command_processor.cpp` L290-304, the same in both
    trees.
  - `exchange(0)` is at L277, before the only return, so T counts every swap. Frame #2 is the first loggable one.
  - The only whole-buffer mark is IssueDraw L3094, counted 1:1 at L3095.
  - Uncounted: `RequestRange(0, kBufferSize)` at L2912-2919, on error-return draws only.
- **Notes and test results:** `build/agent12/p2c-check/NOTE.md`.

### W6 environment record (G11, G12)

```
python build\agent12\w6-gates\w6_env_record.py <W6 matrix out dir> --gate-log bench\agent5\launch\status\window-<id>-<HHmm>.log --json <out>
```

- **Per run** (from sys.json, with run.json as the fallback): scheme, overlay, AC and battery saver at the window's first
  and last row, and any change inside the window.
- **Non-game load per run** = cpu_util_mean × 12 / 100 − the game's cpu_cores_mean. A scored run more than 1.0 core
  above the scored median is flagged.
- **Gate, from Agent 5's launcher line:**
  - `HH:mm:ss quiet gate: STRICT (MsMpEng a/b/c, OfficeClickToRun a/b/c, CrossDeviceService a/b/c)`, or
    `RELAXED (<same>; after N min)`. Both start a window.
  - `GAVE UP` / `DEADLINE (...; window not started)` means no window ran (exit 3).
  - `build/agent1/w5/quiet-check.ps1`'s log (QUIET / NOT QUIET) also works.
  - The tool records the triples, the gate's end time and the gap to the window start (WARN if > 30 min, or if the gate line comes after the start: wrong log?).
    A gate line inside the start minute is 0 min, and a gap across midnight is unwrapped. (Task #24 fix,
    2026-11-23: the old `% 1440` read each night window's gate line, e.g. 00:09:01 for dir `…-0009`, as 1440 min (1439 or 1440 by its seconds),
    so G12 was CHECK in all 7 night windows.)
    An unreadable value (`unreadable`, `n/a`) is recorded as null. A relaxed pass also writes
    `status/relaxed-gate.txt` (run-night.ps1); the window log is `status/window-<wTag>.log` (L567).
- **Last line:** `RECORD: overlay ...; quiet gate ...; non-game load ...`.
- **Exit codes:**
  - 0: OK;
  - 1: the overlay differs between runs, or changes inside a window;
  - 3: a run has no sys data, the gate is not recorded, or no window started;
  - 2: usage, or no results.csv.
- **Tests:** the selftest passes 16/16 (2026-11-23 05:54: the 12 checks of 20:26, which include a GAVE UP line with `unreadable` and `n/a` values, plus 4 gap checks: inside the start minute, across midnight, 43 min across midnight (WARN), and a gate line after the start (WARN)). The W5 record is `build/agent12/w6-gates/w5-env-record.json` (exit 0); see G11
  and G12.

### run_gates: G1-G12 in one command (task #15)

```
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent12\w6-gates\run_gates.ps1 <matrix out dir> [--side <dir>]... [--gate-a <dir>] [--one-bin] [--json <out>] [--brief]
```

- **Same arguments with `python -B build\agent12\w6-gates\run_gates.py ...`.** The wrapper adds the HOLD check (exit 4
  while `perf-notes/WINDOW-HOLD.txt` exists; the script checks too; `-Force` overrides) and Below Normal priority.
- **Read-only.** It writes only the `--json` file.
- **Output:** per-gate details, then one table (gate, status, key number), w6_env_record's `RECORD:` line, and
  `GATES: G1 <status>; ...; exit N`. `--brief` prints only the table and the two last lines.
- **Nothing is tied to W6:**
  - the arms, their bins, cvars and env come from `matrix.json`; the planned runs from `plan.txt`; the finished runs
    from `results.csv`;
  - a gate whose switch no run arm sets is n/a. G4 needs `shared_memory_single_hold_rearm=true` in a run arm; G5-G7
    need `physical_protect_keep_watch=true`.
- **W6 read-out:**
  `run_gates.ps1 <W6 out dir> --one-bin --side <side 1> --side <side 2> [--side <side 3>] --gate-a <gate A> --json <out>`.
  - `--one-bin` makes G2 FAIL unless all run arms use one bin (W6: one S4b bin everywhere). Leave it out for
    matrices that compare bins (W4b).
  - Without `--side` or `--gate-a`, G4 and G5 are PENDING (exit 3).
  - `--json` can go anywhere (e.g. with Agent 8's read-out). Keep it with the window.
- **The launcher's window log** is searched in `bench/agent5/launch/status` (or `--status DIR`, or given with
  `--window-log FILE`). It is matched by, in this order:
  1. the `window <id> END: ... out dir <dir>` line;
  2. a `runner-<tag>.txt` that names the out dir;
  3. a non-dry `START` line within 3 min of the dir's `YYYYMMDD-HHMM`.

  `status-dryrun/` is never used. What the log feeds:
  - G3 checks the END line's runner exit and SUSPECT;
  - G11 quotes the `power scheme at the start:` line;
  - G12 reads the `quiet gate:` line.

  `--gate-log FILE` (any quiet-check log) or `--gate strict|relaxed` overrides the window log for G12.
- **What each gate checks:**
  - G1, MANUAL: each arm's switches beyond the common set, for Agent 10's ratings.
  - G2:
    - each run's bin_dir is its arm's bin;
    - the run's MANIFEST.txt and its exe/dll copies match the bin's by SHA-256 (each bin file is hashed once);
    - with `--one-bin`, the run arms use one bin;
    - a P2 bin has s4-p2c (`p2c_check --bin`);
    - the side runs and gate A are on a matrix or P2 bin, their `exe_sha256` (or exe copy) is the bin's, and they
      share one exe_sha256.
  - G3: results rows = the plan.txt estimate; arms and per-arm counts = plan.txt; each run is OK, exit 0x00000000,
    wm_close, runner exit 0, and has run.json; the launcher's END line says exit 0.
  - G4: `p2c_check` on each `--side` and `--gate-a` dir. The worst verdict counts.
  - G5: gate A sets `physical_protect_keep_watch_verify=true` and has `C1 verify: on` and a first kept protect, with
    0 `C1 verify K:` / `F:` lines.
  - G6 and G7, CODE: met in code. G7 also lists any native-blocked lines seen.
  - G8:
    - 0 stale / write-fault / Protect-failed lines in any run;
    - keep-watch runs and sides are on and keeping;
    - `gate_logdiff` of every run against the merged reference-arm runs: a FAIL finding is FAIL, and NEW
      warning/error kinds are CHECK.
    - The frame-hash check stays by hand.
  - G9: run.json `params.cvar`, args, `env_set` and `toml_set` = the arm's.
  - G10:
    - scored runs are valid and not excluded;
    - each switch's proof line appears once, and never without the switch;
    - no timing-forbidden switch;
    - free RAM ≥ `min_free_ram_gb`;
    - a switch the kit knows no proof line for is CHECK, named in the key (rate and check it by hand);
    - the slow state, as information.
  - G11 and G12: w6_env_record (above).
    - G11 also FAILs when the power scheme, AC or battery saver is not one value in every run, or changes inside
      a window.
    - G12 also flags each run's non-game load above the median + 1.0 core. It is CHECK when the gate line is more
      than 30 min before the window start, or after it (the wrong gate log?). A gate line inside the start minute
      is 0 min (task #24 fix).
- **Exit codes:**
  - 0: everything passes (MANUAL, CODE and n/a allowed);
  - 1: any FAIL;
  - 3: any CHECK, PENDING, NO DATA, NOT RECORDED, NO WINDOW, PARTIAL or ERROR. A kit crash inside one gate makes
    that gate ERROR, with the exception in its key; the other gates still run;
  - 2: usage, or no matrix.json/results.csv;
  - 4: HOLD;
  - 6: the kit itself failed outside the gates. It prints the traceback and `GATES: ERROR; exit 6`. A kit bug is
    never exit 1;
  - with `--expect FIXTURE`: 0 when the fixture holds, else 5.
- **Tests (21:50; re-run 2026-11-23 05:54 after the task #24 G12 fix):**
  - `--selftest` passes 51/51 (49 at 21:50, in 71 s at Below Normal; 2026-11-23: + 2 G12 gap checks). It includes:
    - a synthetic W6-like matrix (s0/p2/p2f/p2fc, side 1, gate A, a launcher log in run-night.ps1's order: STRICT
      gate, scheme, START, END);
    - its fault variant (fallback on side 1, `C1 verify K:` on gate A, a stale line), which makes G4, G5 and G8 FAIL;
    - the checker's cases: a crash inside a gate (ERROR) and outside the gates (exit 6); an unknown switch (G10
      CHECK); a same-size dll with another SHA-256, and a second bin with `--one-bin` (G2 FAIL); a second power scheme
      and AC changing inside a window (G11 FAIL); a gate line 40 min early (G12 CHECK); a side run in the timing
      runner's format;
    - task #24: a gate line inside the start minute (06:50:01, dir `…-0650`) is G12 PASS at 0 min, and a gate line
      5 min after the start is CHECK.
  - W5 and W4b reproduce their fixtures: `EXPECT: OK (57/57)` (exit 0) and `(53/53)` (run exit 1, G10). The fixtures
    also pin each bin's MANIFEST and exe SHA-256 (from Get-FileHash).
  - Details, independent sources and the checker's 13 findings: `RUN-GATES-FIXTURES.md`.

## Gates

| Gate | What | Runs | Proof: what to read | Pass | Owner | Status (20:20) |
|---|---|---|---|---|---|---|
| G1 | Every switch rated | all | b2r: P2 §22 (SAFE OFF; ON output-identical; ON's gate is G4). Fix (i) §23 (SAFE OFF; ON SAFE, not output-identical by design; ON only with C1 (gate B); timed only inside the C1 A/B, b2r L1181, which p2f is, as C1's control arm). C1 v3 row 36/§35. Counter s4-p2c row 31/§30. #7 hash log §20 (side runs only). | all SAFE, ON SAFE to test | Agent 10 | **met**. S4b takes C1 v3 (S4-DRAFT L91, L268) |
| G2 | S4b built; one bin everywhere | all, side 1-3, gate A | Agent 2's build note with the exe/dll SHA-256. The applied game-side `memory_watch.cpp` hashes 70829846… (b2r row 39). The SDK side carries C1 v3: `xmemory.cpp` BCA5E1CF… (`build/agent2/s4b-compose-1932-c1v3.txt` L73-95). The same bin path in all four arms, the side runs and gate A. `p2c_check.py --bin <bin>` says `(this build has s4-p2c)`. | hashes recorded and matching; string found | Agent 2, Agent 8 | pending (bins ~20:30). At the ~19:50 check, `build/agent2/s4b-check/mw/rexlego/src/gpu_native/memory_watch.cpp` was still unpatched (`git apply --check` exit 1, CRLF) |
| G3 | Functional pre-flight | s0, p2, p2f, p2fc | `-PlanOnly`: 13 runs, 4 arms, the real bin, the cvars above. Then one agent `-Quick` pass of all four arms (hidden desktop; functional only). | each boots, reaches the first frame, closes; logdiff NEW 0; p2fc shows the init and first-kept lines | Agent 3 / Agent 8 | pending (Agent 3's queue, to ~22:50) |
| G4 | P2's fallback never runs | side 1, side 2, gate A (side 3 if run) | `p2c_check.py <run dir>` on each run | `RESULT: PASS (total 0)`, exit 0, on each; any WARN quoted | Agent 3 runs; Agent 12 reads | **PASS (22:04), 4 of 4 (side 3 was run)**, all `RESULT: PASS (total 0)`, exit 0, 0 WARN; Agent 3 and Agent 12 agree. Gate A `build/agent3/runs/20261122-210906-w6-gateA-p2fcv-level`: 7271 counter lines, memexport activity in 347 (the level load: real coverage). Side 2 `20261122-211914-w6-side2-p2fc`: 35027 lines, activity 5. Side 1 `20261122-212406-w6-side1-p2f`: 33692 lines, activity 5. Side 3 `20261122-215230-w6-side3-p2fc-attract` (attract mode; 3 rotated logs read oldest first, the process start in game.2.log:28): 36388 lines, activity in 3836 (syncs 30450): real coverage for p2fc. Sides 1-2 reach the title only, so they cover little. Not a W6 arm: s4b23 `20261122-213421-s4b-23-w6-p2fi-level` PASS (total 0), 14063 lines, activity 2695. Outputs `build/agent12/w6-gates/p2c-*.txt` |
| G5 | §21 A: verify | gate A | the gate-A game.log | `C1 verify: on.` present; `C1 keep-watch: first kept protect at` present; 0 `C1 verify K:` or `C1 verify F:` lines (`changed since its upload`) | Agent 3 runs; Agent 10 rates | pending; unblocked (Toy Pad = yes) |
| G6 | §21 B: keep only under G | — | in code: the keep path requires `owns_lock()` | — | Agent 10 | **met** (code) |
| G7 | §21 C: inert on native | — | in code. Positive check if a native run sets keep_watch: `C1 keep-watch: on, but blocked for this process (native renderer)` | — | Agent 10 | **met** |
| G8 | §21 D: on, keeping, nothing stale | gate A, side 2, every p2fc run | `C1 keep-watch: on (with physical_protect_hold_global_lock)` and `C1 keep-watch: first kept protect at` present; no `C1 keep-watch: on, but physical_protect_hold_global_lock is off`. In every run of every arm: no `Recovered stale physical page protection`, `Unhandled guest physical write fault` or `PhysicalHeap::Protect failed`. logdiff NEW 0 against s0; the frame hash or screenshot matches s0 at the same point. | all as listed | Agent 3 (gate A, side 2); Agent 8 (timed runs) | pending. run_gates (22:10, on the real side runs): **FAIL, from gate A only**. Gate A has `[critical] [FATAL] Minidump written to hang-36276.dmp` (game.log:7382, 21:18:20), right after 5 STUCK-LOCK lines; Agent 3's check calls it RECOVERED HANG. This is finding 10 (Agent 1's WARN). Sides 1-3 have no fail pattern and no [critical] line. Keep-watch is on and keeping in 3/3 (gate A, sides 2-3; rotated logs read). If the WARN stands, read the gate-A FAIL as WARN by hand, or re-run gate A clean |
| G9 | Launch-only switches | all | the cvar list the runner records per run; hands off, no dev console. C1 v3 latches `physical_protect_keep_watch` and `physical_protect_hold_global_lock` at init (kInitOnly), so a console set never reaches Protect. `physical_protect_keep_watch_verify` is still read live, and no other cvar is latched: for those the rule stays hands-off. | recorded list = the arm's | Agent 8 | procedural |
| G10 | Per-run validity | every timed run | S4-DRAFT L323-327: the slow state per run; each ON arm's log line (p2fc: the init and first-kept lines, no `C1 verify: on`); ≥ 6 GB free (runner; ≥ 8 GB on the user's check); Defender below ~5 % (see G12) | all, per run | Agent 8 | per run |
| **G11** | **Power overlay** (new) | every timed run | `w6_env_record.py` (Tools): overlay, scheme, AC and battery saver per run, from sys.json | one overlay, scheme and AC in all 13 runs, no change inside any window (the runner already excludes a run on power_change); `RECORD: overlay <x> (13/13, no change)` | Agent 8 runs the tool; Agent 12 owns it | tool ready. **W5: best_efficiency 16/16**, Balanced 16/16, AC 1 16/16, saver 0 16/16 |
| **G12** | **Quiet gate: strict or relaxed** (new) | the W6 window | the launcher's gate line in `bench/agent5/launch/status/window-<id>-<HHmm>.log` (also in `status/log.txt` and `status/gate.txt`; a relaxed pass also writes `status/relaxed-gate.txt`; never `status-dryrun/`), read by the same command | the record says STRICT or RELAXED (both are valid; GAVE UP / DEADLINE = no window, exit 3). Recorded: the mode, the MsMpEng / OfficeClickToRun / CrossDeviceService triples, the gap from the gate to the window start, and each run's non-game load with the > median + 1.0 core flag | Agent 8 runs the tool; Agent 12 owns it | tool ready. **W5: RELAXED** (NOT QUIET after 20 min at 17:51:55; Defender 0.77-1.14 cores, last 10 samples 0.88-0.99; the window started 4 min later). Non-game load 3.01-4.14 cores (median 3.30), none flagged |

**G11 and G12 in the read-out:**
- **G11 differs from W5:** if W6's overlay is not best_efficiency, compare W6 only within itself, not with W5's absolute
  numbers.
- **G11 MIXED (exit 1):** report it, and read the pairs only over the rounds in which all four arms ran on one overlay.
- **G12 RELAXED:** Defender was at ~1 core through the window. A steady load hits all four arms alike and the
  round-robin balances it, so the pairs stay valid. R7 says so and quotes the MsMpEng triple.
- **Flagged runs** (more than 1.0 core above the median non-game load): R3 also gives each pair's verdict without the
  rounds that hold a flagged run.

**What a G4 result means:**
- **Only PASS is a pass.**
  - NO DATA: the run had no `slow_frame_log_ms`, or the bin has no s4-p2c.
  - PARTIAL: a process with no counter lines, or two builds in one log.
  - In both cases, fix the cause and re-run. ERROR: send the run dir to Agent 12.
- **FAIL:** Agent 1 decides a cap (b2r §22) before p2, p2f or p2fc is timed. See the decision table.
- **PASS with a WARN:** still a pass, but quote the WARN. A tail WARN means frames after the last counter line are
  unchecked.
- **Coverage:** a PASS covers only the scenes the run went through. The script prints the memexport activity, so R6 can
  say which. On S4a:
  - the title showed activity in 5 of 74714 slow-frame lines (syncs 5, 1208 KB), so a title PASS is weak;
  - the attract route showed it in 3626 of 28704 (invalidations on memexport pages 5373x, 26294644 KB; syncs 16537,
    648548 KB).
  - Gate A's level load and side 3's attract scene are the real coverage.

**Decision table (Agent 1 decides):**

| G4 | C1 (G5 and G8) | timed run |
|---|---|---|
| PASS | go | `-Only s0,p2,p2f,p2fc -Repeats 3` (13 runs) |
| PASS | no-go | `-Only s0,p2 -Repeats 6` (13 runs; Agent 5's contingency) |
| FAIL, cap set | go | rebuild with the cap, redo G2-G4, then row 1 |
| FAIL, no cap | go | arms without P2: `f` = `physical_protect_hold_global_lock=true`; `fc` = f's + `physical_protect_keep_watch=true`, `physical_protect_keep_watch_verify=false`. `-Only s0,f,fc -Repeats 3` (10 runs, ~25 min). C1 = fc − f still has fix (i) on both sides; fix (i) = f − s0, read from C1's control arm as p2f − p2 is. Needs 2 new arms in the matrix. |
| FAIL, no cap | no-go | Agent 1's call. **v1's option "s0 vs f only" conflicts with b2r L1181:** fix (i) is timed only inside the C1 A/B. It would need Agent 10 first; otherwise there is no W6. |

## Read-out steps

1. **R0 Pre-flight, before the window.** Fill in G1-G9. Save the `-PlanOnly` output and the bin hashes (G2) with the
   window.
2. **R1 Validity and environment (G10, G8's log lines, G11, G12).**
   - Simplest: `run_gates.ps1` (Tools) on the W6 matrix dir, with `--side` and `--gate-a`, gives G1-G12 in one table
     with w6_env_record's RECORD line. Keep its `--json` with the window.
   - Or run `w6_env_record.py` (Tools) on the W6 matrix dir with the window's launcher log. Keep its JSON with the window.
   - A run that fails G10 or G8 is redone or dropped, with the reason written down. Never read fps from a failed run.
3. **R2 Per arm.** Take the median of 3 and the min-max range for:
   - GPU Commands ms/f (`threads.csv`): the main metric;
   - Main ms/f: second, because C1 swaps Main's lock-time protects for write faults;
   - fps and the slowest frames (`perf.csv`, `summary.md`).
4. **R3 Pairs.** All on the same bin:
   - P2 = p2 − s0;
   - fix (i) = p2f − p2;
   - C1 = p2fc − p2f;
   - stack = p2fc − s0.

   - **What to report:** the difference of medians plus the 3 per-round differences (round-robin, so every round has one
     run of each arm). With a flagged run (G12), also give each verdict without the rounds that hold it.
   - **Noise rule:** if the two arms' min-max ranges overlap, write "no detectable change" with the median difference
     in brackets. 3 repeats can't make a small P2 or fix (i) effect significant.
   - **Expected:**
     - C1 up to −3.40 / −3.59 ms/f on GPU Commands in the slow state (~−0.85 to −1.2 at normal clocks);
     - fix (i) 0.003-0.17 ms/f;
     - P2 small (README).
5. **R4 Kept protects per frame.**
   - **Side 2:** `C1 keep-watch: N protects kept so far` is cumulative, and printed at powers of 2 and then at every
     multiple of 4096. Pair each such line with the frame index of the slow-frame line just before it. Then
     kept/frame = ΔN / Δframe between the first and last pair inside 70-220 s.
   - **Timed p2fc runs:** these have no slow-frame lines. Take ΔN / Δt from the timestamps, divided by the run's fps, as a
     cross-check (resolution 4096).
   - About 1.6/frame means the ring case (CB/f 1.59). About 17 means the game rewrites the whole buffer (B/f 16.67).
6. **R5 Realised u.**
   - Run `python bench/agent12/s4_uhash.py <run dir>` (default window `--from 70 --to 220`) on side 1 and side 2.
     Neither output may have a `warning` key.
   - u = 1 − `upload_kb_per_frame.mean`(side 2) / `upload_kb_per_frame.mean`(side 1). Compare it with u_block 0.934
     (S4a title; b2r 0.9336). An identical rewrite still faults under C1, so u ≤ u_block, and the gap is the
     identical-rewrite share.
   - Cross-check: s4_uhash.py does not parse the cpu-write field, so use `python bench/agent5/s4_slowframe.py <run dir>`
     and its `inval_kb_per_frame.mean`.
     - Side 1 should read ~3848 KB/f, against the hash log's 3844.
     - Side 2 should fall with the hash log's KB/f. If it stays near 3848, kept protects are not taking effect.
7. **R6 P2 counter.** For side 1, side 2 and gate A (and side 3), report `p2c_check.py`'s RESULT line, its WARNs and its
   memexport activity line. Timed runs give NO DATA by design, because `slow_frame_log_ms` is never on in a timing arm.
8. **R7 Report** to Agent 1 (copy Agents 5, 10 and 11):
   - the arm table: median [min-max] for GPU Commands, Main, fps and the slowest frames;
   - the pair table, with the noise verdicts (and without flagged rounds, if any);
   - kept/frame, realised u, and the G4 result with its coverage;
   - the gate statuses G1-G12, with G11's overlay and G12's mode quoted from the RECORD line;
   - caveats:
     - u is title-only;
     - compare W6 within itself, not with window 3, and not with W5's absolute numbers if G11's overlay is not
       best_efficiency;
     - if G12 is RELAXED, the steady Defender load (above).

## Changes for Agent 5's draft

- **(a) C1 v3 is settled** (S4-DRAFT L91, L268; b2r row 36/§35).
  - README gate 1 still says "C1 v2 rated (b2r row 35 / §34)", with v2's console caveat.
  - README gate 2 still says "C1 v2 ... then `keep-watch-v2.diff`".
  - The matrix notes say "C1 v2" at matrix-w6.json L20, L22, L38 and L42.
  - With v3, keep_watch and hold_global_lock are latched at init; `_verify` is still read live (G9).
- **Stale S4-DRAFT cites** (S4-DRAFT moved by 58 lines): L288 → L346, L270 → L328, L264 → L322, L280 → L338,
  L265-269 → L323-327. For S4-DRAFT's owner: its W6 row (L346) still says "C1 v2", while L268 says v3.
- **(b) G4 coverage:** read the counter on side 2 and gate A (with `slow_frame_log_ms=1` added), not only on side 1.
- **(c) Kept/frame:** R4's pairing on side 2. The timing arms are only a cross-check.
- **(d) The tools** and their exit codes (Tools). New since 17:05: PARTIAL (3) and ERROR (4); only PASS is a pass.
- **(e) The counter is in S4b:** G2's `--bin`.
- **(f) Pre-flight:** `-PlanOnly` plus a `-Quick` functional pass of all four arms (G3).
- **(g) If G4 fails and no cap is set:** arms without P2 (decision table), but not "s0 vs f only" (b2r L1181).
- **(h) The noise rule** (R3).
- **(i) G11, power overlay** (Agent 1, 19:31): keep `"sys_csv": true`, and record with `w6_env_record.py`.
- **(j) G12, quiet gate** (Agent 1, 19:31): the launcher's gate line, read by the same tool, and RELAXED's caveat (R3, R7).
- **(k) Side 3** (suggested): the attract route, for G4 coverage.
- **(l) G2's source hashes:** the game-side `memory_watch.cpp` 70829846… (b2r row 39) and the SDK `xmemory.cpp`
  BCA5E1CF….
- **(m) R5's fields:** `upload_kb_per_frame.mean` from s4_uhash.py; the cross-check from
  `bench/agent5/s4_slowframe.py`'s `inval_kb_per_frame.mean`.
- **(n) G8's bad lines** add `PhysicalHeap::Protect failed` (b2r L1178).

## Log strings (keep-watch-v3.diff; v3 adds none to v2's; re-checked against the diffs)

- `C1 keep-watch: on (with physical_protect_hold_global_lock)`: INFO at init (Memory::Initialize). Printed only when
  keep_watch and hold_global_lock are both on and the process is not blocked.
- `C1 keep-watch: on, but physical_protect_hold_global_lock is off, so no protect is kept`: WARN.
- `C1 keep-watch: on, but blocked for this process (native renderer)`: INFO at init, when keep_watch is on in a blocked
  (native) process.
- `C1 keep-watch: first kept protect at {:08X}, {} bytes`: INFO, once (kept == 1).
- `C1 keep-watch: {} protects kept so far`: printed at powers of 2 and at every multiple of 4096.
- `C1 keep-watch: blocked for this process (native renderer); every protect takes the normal path`: INFO, once per
  process, at the first protect that reaches ProtectKeepWatch in a blocked process (so only with hold_global_lock on).
- `C1 verify: on. Hashing CPU uploads; K checks keep-watch protects, F checks write faults`: INFO, printed on the first
  record.
- `C1 verify {K|F}: page {:08X} changed since its upload ({} so far){}`: WARN.
  - K lines always end `; protect keeps the normal path`; F lines never do.
  - K and F are counted separately, and each prints 1-256, then every 4096th.
- Bad lines: `Recovered stale physical page protection`, `Unhandled guest physical write fault`,
  `PhysicalHeap::Protect failed` (b2r L1178).
- P2 and fix (i) print no line of their own. The proof that they are ON is the runner's cvar list. p2fc's init line also
  shows that fix (i) is ON.
- The counter's field: ` | memexport full-buffer {}x (total {})` at the end of the slow-frame line.
