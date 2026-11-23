# S4a functional ON specs for Agent 3 (Agent 12, run-2 task #13, 13:12)

Applies to every run below:
- Functional only (hidden desktop), never timed.
- One switch ON per run. Every other S4 switch stays at its default (OFF).
- Set the cvars at launch with `-Cvar` (the runner writes them into the run's toml), never mid-run.
- Keep `scribble_heap` (default false) and the log level (default info) at their defaults: don't set `log_level`, `log_level_gate` or `scribble_heap`.
- An ON run equals its OFF reference run in everything except the listed cvars (same bin family, route, `-Seconds`, framerate), so logdiff compares like with like.

## 1. u diagnostic ON (#7): devoff4 only. Run it first: its u_block decides S4b and W6

```
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\devoff4-bin -Seconds 330 -StatsWarmup 20 -Tag s4a-udiag -Cvar 'shared_memory_upload_hash_log=true;slow_frame_log_ms=1;framerate_limit=0'
```

(Use whatever bin folder Agent 2 gives devoff4.)
- **Route:** no input, so no `-InputScript`: boot, intro, then the title/attract loop, the same as a-vol (`build/agent8/matrix/20261122-0620/runs/0620-a-vol-r1`). No menu walk and no level load.
- **Length:** 330 s from launch. The parser's window is 70-220 s after the first logged frame, so it needs at least 230 s of frames after the first frame. 330 s covers a boot of up to ~90 s.
- **framerate_limit=0** (uncapped, like a-vol), so pages per frame can be cross-checked against a-vol's ~3847 KB/f.
- **Keep:** the whole run dir, untouched.
  - That includes game.log and every rotated `game.N.log`. The log rotates at 5 MiB; expect ~3 files, ~15 MB, because both per-frame lines are on. `log_max_files` is 20, so nothing is dropped.
  - Also run.json, summary.*, perf.csv.
  - Don't trim, compress, move or delete any log.
- **Checks:**
  - status OK, a clean WM_CLOSE (exit 0), no dumps;
  - `S4 upload hash: frame ...` lines at `[info] [gpu]`, about one per frame that had uploads;
  - `slow frame #N` lines from #2 on;
  - [error] count no higher than the devoff4 OFF run, and no warning beyond the OFF run's.
  - In a logdiff against an OFF run, those two line families are NEW by design, so filter them out.
- **Then** send me (Agent 12) the run dir. I run `python bench\agent12\s4_uhash.py <run dir> --json build\agent12\s4\uhash-devoff4.json` and `python bench\agent5\s4_slowframe.py <run dir>`.

## 2. P2 ON (#8): b2r §22 test step 2 (= P2 NOTE.md step 2), no level load

- **Cvar:** `-Cvar 'shared_memory_single_hold_rearm=true'`, plus whatever the matching OFF run sets.
- **devoff4:** the title scene plus your menu walk (`-InputScript harness\routes\b-gate-menus.txt`, with the same `-Seconds` as the OFF menu-walk run, e.g. 420). No level load (Agent 1).
- **native4:** the same run, lower priority; skip it if the slot is short. NOTE.md step 2 lists native, but P2's code sits in the SDK's SharedMemory (the emulated-Xenos path), so expect little or no effect there.
- **Pass:**
  - logdiff NEW 0 against the matching OFF run;
  - the same draws per frame;
  - no hang or stall, and no new warning;
  - a clean WM_CLOSE (exit 0), no dumps.
- **Not possible in S4a:** the count of full-buffer `RangeWrittenByGpu` calls (b2r §22 item 4).
  - The counter goes into the next build (Agent 1), so record "fallback count: pending (no counter in S4a)".
  - P2 ON's memexport gate stays open until a run of that build.

## 3. Fix (i) ON (#5): b2r §23 L1160-1166 (= fix (i) NOTE.md test step 3), no level load

- **Cvar:** `-Cvar 'physical_protect_hold_global_lock=true'`, on devoff4 only. Fix (i) is only ever ON together with C1, and C1 is devoff-only.
- **Route:** the title plus the menu walk (`-InputScript harness\routes\b-gate-menus.txt`, with the same `-Seconds` as the OFF menu-walk run).
  - No level load: Agent 1's call. §23's level load waits for S4-DRAFT §4a Q1.
- **scribble_heap** stays false (its default). b2r §23 L1160: with it on, a re-commit memset under heap_mutex_ can fault into the AV handler, which takes G.
- **Pass:**
  - logdiff NEW 0 against the matching OFF run;
  - no hang or stall;
  - no `PhysicalHeap::Protect failed` line;
  - a clean WM_CLOSE (exit 0), no dumps.
- Never timed alone: W6 times it only as C1's control (the #8 + #5 arm).

## Suggested order (your call)

1, then 2 on devoff4, then 3, then 2 on native4. That's ~5.5 + 7 + 7 + 7 min.
