# P2 counter check: `p2c_check.py`

Agent 12. Written for task #32 (16:59). Revised for task #11 (run 2) at 19:57, after a read-only check against the
counter's source. **Tests: 13/13 PASS at 20:26** (`test-results-20261122-202629.txt`; the 19:42 run of the first version
and the 20:12 run were also 13/13).

## What it reads

The field that s4-p2c adds to ReportSlowFrame's line. The diff is
`build/agent12/s4-p2c/memexport-full-buffer-counter.diff` 29E02E24… (rated SAFE, b2r row 31/§30):

```
slow frame #N: X ms | ... | memexport syncs S (K KB), on demand D (K KB) | memexport full-buffer Fx (total T)
```

- **F** is the number of memexporting draws in that frame with no known destination range. For each one, IssueDraw calls
  `shared_memory_->RangeWrittenByGpu(0, SharedMemory::kBufferSize)` (L3094), and the diff adds a relaxed `fetch_add`
  right after that call (L3095).
- **T** is the running total since process start (a function-static). ReportSlowFrame takes F with an `exchange(0)` on
  every swap (L277), before the threshold test and the only return. So T also counts frames that were not logged and
  frames in rotated logs that are gone.
- **When it prints:** only with `slow_frame_log_ms` set (use 1), and only in builds with s4-p2c (S4b). It does not
  depend on P2's cvar: it counts the path with P2 ON or OFF.
- **Line numbers** are in o1-v3/o2-v3 `src/graphics/d3d12/command_processor.cpp` (identical in both trees).
  - The format is REXGPU_INFO at L290-304. The selftest builds every line from `REAL_FORMAT`, a copy of L291-296.
  - Logs use the pattern `[%Y-%m-%d %H:%M:%S.%e] [%l] [%n] [t%t] %v`, at info level, with flush_on(info).

## Usage

```
python build\agent12\p2c-check\p2c_check.py <run dir | log files, oldest first> [--json OUT] [--bin PATH]
python build\agent12\p2c-check\p2c_check.py --selftest
```

- **A run dir** is read as `game.N.log` ... `game.1.log`, then `game.log`, oldest first. If none of these exist,
  `log.txt` is read instead. Log files given explicitly are read in the order given.
  - spdlog rotates at 5 MB × 20 files with rotate_on_open=false, so a relaunch appends to `game.log`.
  - If a run's `log_file` cvar is empty, the game logs to `logs/<app>_NNN.log`. Give those files explicitly, oldest
    first.
- **Processes:** a new process starts at a `] Startup: launching the module` line, where the frame index restarts, or
  where T falls. For each process the script prints:
  - its start, its first and last frame and their lines;
  - its counter and no-field line counts;
  - T, split into F on logged lines and frames not logged;
  - the first frame with T > 0;
  - the last counter line, and how long the log goes on after it.
- **The `log time range:` line** shows when the logs were written, so a stale `game.log` from another run is easy to
  spot.
- **WARNs** (they don't change the RESULT; quote them):
  - the log goes on more than 5 s after a process's last counter line (`TAIL_WARN_S`): frames after it are unchecked;
  - a process's last slow-frame line has no field: cut off at exit;
  - more than one process (their totals are added);
  - T falls with no index restart;
  - T rises by less than the frame's F.
- **A note** is printed when the first logged frame is > #50. If the process start is not in the logs, older rotated
  logs are gone; if it is, `slow_frame_log_ms` was above 1. T still counts those frames.
- **The memexport activity sums** come from the same lines: invalidations on memexport pages, syncs, and on demand. Any of
  them > 0 means memexporting draws with known ranges ran in the logged frames. All 0 proves nothing about coverage.
- **`--bin PATH`** (a file or a dir, subfolders too) checks whether the .exe/.dll files contain the format string
  `memexport full-buffer {}x (total {})`, i.e. whether the build carries s4-p2c. It prints relative paths and is
  informational only.
- **`--json OUT`** writes the full result.

| RESULT (last line) | exit | meaning |
|---|---|---|
| `PASS (total 0)` | 0 | the fallback never ran, up to the last logged frame |
| `FAIL (total N)` | 1 | it ran; P2 ON waits for Agent 1's cap decision (b2r §22) |
| `NO DATA` | 3 | no slow-frame lines (`slow_frame_log_ms` unset, or the log level hides info lines); lines without the field (no s4-p2c); or no log found |
| `PARTIAL` | 3 | T = 0, but some process has no counter lines, or lines with and without the field (two builds in one log) |
| `ERROR` | 4 | the script itself failed (an exception); not a FAIL |
| (usage error) | 2 | |

**Only PASS is a pass.** NO DATA and PARTIAL mean: fix the run and re-run.

## The independent check (task #11, read-only subagent)

- **It agreed on all 10 points** against the source: the format; `exchange(0)` before the only return; frame_index is
  static and increments every swap, and the first call always returns, so #2 is the first loggable frame; the only
  caller is IssueSwap L2224; the only whole-buffer mark, counted 1:1; the log pattern, level and flush; rotation.
- **Uncounted edge:** `RequestRange(0, kBufferSize)` at L2912-2919 runs on error-return draws only. It is not the P2
  fallback path.
- **It found four ways to get a false PASS, all fixed in the 19:57 revision:**
  - frames logged after the last counter line: the tail WARN;
  - a process with no field lines next to one with T = 0: PARTIAL;
  - a stale `game.log`: the log time range line;
  - cut lines: the cut-off check now runs per process.

## Tests

`build\agent12\p2c-check\run_tests.ps1` runs 13 tests at BelowNormal and stops if `perf-notes\WINDOW-HOLD.txt` exists.
The 20:26 results:

| # | test | result |
|---|---|---|
| 1 | `--selftest`: 16 synthetic CRLF cases + 8 more checks | **24/24** |
| 2 | S4a u-diag `build/agent3/runs/20261122-133730-s4a-udiag` (S4a has no s4-p2c) | NO DATA, exit 3: 74714 slow-frame lines, none with the field. Process 1 started at game.8.log:29, frames #2..#75014. Memexport activity in 5 lines (syncs 5, 1208 KB) |
| 3 | S4a attract `...140637-s4a-udiag-attract` | NO DATA, exit 3. Memexport activity in 3626 of 28704 lines (invalidations on memexport pages 5373x 26294644 KB; syncs 16537, 648548 KB) |
| 4 | W5 timed run `build/agent8/matrix/20261122-1756/runs/1800-s0-r1` | NO DATA, exit 3: no slow-frame lines (by design in a timing arm) |
| 5 | missing run dir | NO DATA, exit 3 |
| 6 | no arguments | usage, exit 2 |
| 7 | `--bin build/agent2/devoff4-bin` (S4a) | the string is in none of its 4 .exe/.dll files |
| 8 | `make_fixtures.py`: real u-diag lines plus the field in `REAL_FORMAT` | pass, fail (final T 5) and cut written to `fixtures/` |
| 9 | fixture pass | PASS (total 0), frames #2..#75014 |
| 10 | fixture fail (F 2 at slow line 10, +3 unlogged by slow line 20) | FAIL (total 5): "F on logged lines 2, in frames not logged 3"; first T > 0 at game.8.log:57, frame #11 |
| 11 | fixture cut (the last line without the field) | PASS (total 0) + `WARN: ... cut off at exit?` |
| 12 | `w6_env_record.py --selftest` (case 10: a GAVE UP line with `unreadable` and `n/a` values) | 12/12 |
| 13 | `w6_env_record.py` on W5 + `build/agent1/w5/quiet-1731.log` | exit 0: `RECORD: overlay best_efficiency (16/16, no change); quiet gate RELAXED; non-game load 3.01-4.14 cores` |

## Pending (after Agent 2's S4b bin and Agent 3's runs)

- `--bin <S4b bin>`: expect `(this build has s4-p2c)` (W6 G2).
- Side 1, side 2 and gate A with `slow_frame_log_ms=1`: the W6 G4 verdicts. Side 3 (the attract route) is suggested for
  coverage.
