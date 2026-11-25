# M8 staged runner improvements: safety rating

M10 (successor of Agent 10), 2026-11-25 ~02:15. Read-only. Nothing was run, built or installed.

## Files rated

| file | sha256 (first 16) | bytes |
|---|---|---|
| staged/run-matrix.ps1 | 72370A1E737A3A34 | 57456 |
| staged/run-matrix.diff | 1038DE52317B1E58 | 16160 |
| staged/frame_summary.py | 987E0EC03456D5DC | 12859 |
| staged/frame_summary.diff | 2E32EDDD57EDEDD6 | 3649 |
| staged/drivers/LdSys.cs | 4EFD5C91B5DF3F68 | 65464 |
| staged/LdSys.cs.diff | A4890BD480CC8A2F | 19280 |
| staged/drivers/sys-csv.ps1 | F3F06AB013F2423E | 12192 |
| staged/sys-csv.ps1.diff | 4EA25AE821D2D175 | 7305 |
| staged/sys_summary.py | 6FCE3630B13134D5 | 16533 |
| staged/sys_summary.py.diff | B930659A15AF75DD | 12955 |
| staged/RUNNER-NOTES.md | 20E9A688CA75445B | 4208 |
| staged/SAMPLER-NOTES.md | 16548A673E712D68 | 11572 |

`staged/` = `build/agent8/session3/staged/`.

## Base

These are the current `bench/agent8/run/` files at 02:11. All five diffs match a fresh `git diff --no-index` of base vs staged, so nothing drifted.

| base file | sha256 (first 16) |
|---|---|
| run-matrix.ps1 | 1A522CDFE9DC36F8 |
| frame_summary.py | 0A7D35873E88E50E |
| drivers/LdSys.cs | B452D25872E76ACC |
| drivers/sys-csv.ps1 | 017A4F3EB6252983 |
| sys_summary.py | C95767DE04CB95E4 |

Read for context, not rated:

| file | sha256 (first 16) |
|---|---|
| run-timing.ps1 | 75F4B5278BD75C14 |
| selftest/sys_selftest.ps1 | 216DE7F4D91A69EF |
| bench/agent5/launch/run-night.ps1 | (pin logic L183-213, L967-974) |

## Verdict

**SAFE-IF**, for an off-night install (no launcher and no run-matrix running), under conditions C1-C5.

| piece | verdict |
|---|---|
| run-matrix.ps1 (warm-up runs, new columns) | SAFE-IF C1, C3, C5 |
| frame_summary.py | SAFE |
| sampler: LdSys.cs + sys-csv.ps1 + sys_summary.py | SAFE-IF C1, C2, C4, C5. Install all three together. |

None of the pieces touches other processes (see "Process touching"). None can crash the game or a window. The worst failure is a dead sampler, which gives the info flag `sys_missing`.

Expected timing changes:
- run-matrix with `warmup_runs` 0 produces a byte-identical plan (M8's AST test).
- frame_summary: every old key is unchanged except `share_lt_light`, which is now unrounded.
- The sampler adds measurable but small load to sys_csv rows: see S1.

### Conditions

- **C1 (install):**
  - Install only while no run-night.ps1 or run-matrix process runs and no window is in progress.
  - Re-check the five base hashes above first.
  - Copy LdSys.cs, sys-csv.ps1 and sys_summary.py in one step. A new sys-csv.ps1 with the old LdSys fails at `[LdSys]::ProcEvery`: init exit 1, then `sys_missing`.
  - After install, restage the planned windows (`stage-window.ps1 -PlanOnly`). The launcher pins every .py/.cs in run/ and all of drivers/ (run-night L184-193), so any copy made while the launcher is up refuses its next window. That failure is safe but loses the window.
- **C2 (selftest):** before anyone uses `selftest/sys_selftest.ps1` as a check, patch it to the 31-column header. Today it hard-codes the 24-column header (L27; exact compares at L151 and L225), so after install it fails falsely. That file is M8's, outside the staged set.
- **C3 (comparability):** never compare rows from a window with warm-ups against rows from one without. Never compare sys_csv rows from before the install against rows from after it in one comparison. Round 1's GPU/thermal state differs with warm-ups, and the sampler cost differs (S1).
- **C4 (first smoke must pass before any timed window uses the new sampler):** see "First smoke run" below. If the snapshot check fails, set the `-ProcEvery` default in sys-csv.ps1 to `0`. That is a one-line change and keeps nongame_cores/game_cores/disk_MBps, which cost O(1) per row.
- **C5:** the run-loop code for warm rows is untested (RUNNER-NOTES L41). The first use of `warmup_runs > 0` must be the smoke run, not a scored window.

## What I checked

1. **LdSys.cs diff in full (+215/-7).**
   - Offsets checked against the x64 SYSTEM_PROCESS_INFORMATION layout: CreateTime 0x20, User 0x28, Kernel 0x30, ImageName 0x38/Buffer 0x40, Pid 0x50, ReadTransfer 0xE8, WriteTransfer 0xF0, entry size 0x100.
   - Parse loop bounds: `off + 0x100 <= ret`; `next <= 0` ends the loop.
   - Buffer growth on STATUS_INFO_LENGTH_MISMATCH: 4 attempts, then the snapshot fails with blank cells and a fresh baseline.
   - ProcSnap and SysCores are wrapped in try/catch both in Init and per row.
   - The buffer is freed in cleanup.
   - The 7 new header columns match the 7 commas appended per row.
   - Process names go through `Clean()` (removes `,` `"` and control chars), then `:` `;` and space become `_`. So top lists can't break the CSV or `parse_top`'s `rsplit(":", 2)`.
   - Snapshot rows are Rows 0, 5, 10, ... (`Rows++` at L981 comes after the write). Row 0's rates come from the Init baseline.
2. **sys-csv.ps1 diff.**
   - `-ProcEvery` is validated (0..3600). Two extra fields in the start and timing lines.
   - The stop line is unchanged, so run-timing's `^sys-csv: stop` parse (L503) is unaffected.
   - The new repo-root walk finds the same WS root from `bench/agent8/run/drivers`.
   - The new dll `LdSys-4efd5c91.dll` is already in `build/agent8/cache` (02:00), so no compile at the first run.
3. **sys_summary.py diff.**
   - Old CSVs give null proc keys, and the summary line is unchanged for them.
   - `header_ok` accepts both headers.
   - `nongame_load` is added to the flags. run-timing L592-598 puts every flag outside `$sysExcluding` into flags_info, so it is **INFO only** and never excludes a row.
   - run-timing passes no `--nongame-thr`, so the default 2.8 applies.
4. **frame_summary.diff.**
   - Only adds over_8/10/16_7ms and frames_lt_light, and drops the 4-dp rounding of share_lt_light.
   - run-timing copies frames.json whole, and `light_share_high` is info (L587).
5. **run-matrix.**
   - The diff was read in full.
   - Warm runs: plan formula (the last warm run = the arm before round 1's first); `scored = not (cold or warm)`; `kind` column.
   - Summary filters use `scored -eq 'True'`; the warm label shows in the run and flag tables.
   - `N()` with 15 digits is in range for Math.Round.
   - Export-Csv rewrites the whole file from `$rows`, with no resume or Import-Csv, so the column order is stable.
   - Seeding (L660-667): see N1.
   - sys_csv only runs when the matrix sets `sys_csv` (L496).
6. **Consumers of results.csv.**
   - `matrix_recheck.py` keeps only `scored == true` (L239-253), so warm rows are dropped. Only the label is wrong (N2).
   - `bench/agent5/load_phase.py` classifies by tag: `warm<j>-<arm>` is neither `cold-` nor `<arm>-r<k>`, so it becomes its own pseudo-arm and is never merged into a real arm (N3).
   - No other script under bench/agent5, bench/agent8, build/agent3, agent6, agent9 or agent12 reads results.csv.
7. **M8's offline sampler test outputs** (`staged/test/*/sys.out.txt`): see S1.

## Process touching

- **Sampler:**
  - New calls: `NtQuerySystemInformation(SystemProcessInformation)`, which is read-only and opens no handle to any process (Minecraft included); `GetSystemTimes`; `GetProcessTimes` on the existing game handle (`SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION`, L536).
  - No new OpenProcess, no Kill/Terminate, no child process, no priority change. The sampler thread priority is unchanged (normal, as before).
- **run-matrix:** process handling is unchanged. It only waits up to 90 s for `legodimensions` to exit, as before.

## Findings

- **S1 (SHOULD): snapshot wall-time stalls, and the snapshot is ON by default in every sys_csv row.**
  - run-timing starts sys-csv.ps1 without `-ProcEvery` (L235), so after install every sys_csv run takes a snapshot every 5th second. No matrix or run-timing knob turns it off.
  - CPU cost is small:
    - snapshot ~10.7 ms CPU (`parts_cpu_mean proc`);
    - steady sampler CPU 0.38% of one core at every=5 (cmp-new5), vs 0.16-0.22% for the original (smoke-orig, cmp-orig) and 1.29% at every=1.
  - Wall time is not small. `sample_ms_max` in M8's tests was:

    | test | sample_ms_max (ms) |
    |---|---|
    | cmp-new5 | 351 |
    | smoke3 (every=5) | 383 |
    | smoke2 | 468 |
    | smoke (every=1) | 466; `proc` part max 459; skipped=2 |
    | originals | 4.6-13.6 |

  - The tests ran 01:54-02:06 alongside M3's functional runs and user apps, so the stalls are most likely preemption under load. Kernel lock waits inside the walk can't be ruled out offline. The game itself is never blocked by a read-only snapshot as far as the code shows.
  - Result: the sampler is very unlikely to change frame timing, but this is unproven. Hence C4: prove it on an idle machine, or fall back to `ProcEvery 0`.
- **N1: seeding from warm rows.** The seed source is the last OK/PROFILE row of `seed_arm` (L664), which can now be a warm row.
  - Behaviour changes in one case only: in round 1, a seeded arm that runs before its seed arm used to be SKIPPED ("no completed run") and now seeds from the seed arm's warm run.
  - A warm run is a full-length run on the same bin, so the cache is equivalent. Cold rows were already eligible.
  - Acceptable. Record it in the window notes when it happens: `seed_from` names a `warm*` run dir.
- **N2:** `matrix_recheck.py` labels warm rows "unscored (cold)". Cosmetic; M8 already noted it.
- **N3:** `load_phase.py` (Agent 5's) lists warm runs as pseudo-arms `warm<j>-<arm>`, with extra comparison lines. Cosmetic. If you want it clean, the owner should treat the `warm` prefix like `cold-`.
- **N4:** unrounded `share_lt_light` can flip the info flag `light_share_high` only for values in [0.59995, 0.6). Never excluding.
- **N5 (privacy):** `top_cpu`/`top_io` write the names and pids of the user's busiest processes into every sys.csv. Fine locally. Don't publish run dirs or sys.csv/sys.json outside the WS.
- **N6:** a malformed snapshot entry would raise an AccessViolation in `ProcName`, which .NET Framework does not deliver to `catch (Exception)`. That kills the sampler only, giving `sys_missing` info; the game and run are unaffected. A theoretical risk, since the kernel fills the buffer.
- **N7:** `nongame_load` (window mean nongame_cores >= 2.8) is a useful host-noise marker. Keep it INFO. Making it excluding would change which rows count; that is a separate decision needing a fresh rating.

## First smoke run (must verify)

Use a quick matrix, sys_csv on, `warmup_runs 1`, 2 arms. Run it on the hidden desktop or in a day slot, never as a scored window. Check each item:

1. Before install, the base hashes still match. After install, `pins.txt` refreshes at the next launcher start.
2. With `warmup_runs` 0 or absent, the plan printout is identical to the old runner's.
3. Warm rows have `kind=warm`, `scored=False`, `round=0` and tag `warm1-<arm>`.
   - They are absent from the summary numbers and shown as `warm` in the run and flag tables.
   - The run order puts no arm twice in a row across the warm-up/round-1 boundary.
4. results.csv has the new trailing columns (`kind, over8, over10, over16_7, frames_lt_light`), filled in scored rows. `light_share` has full precision.
5. `matrix_recheck.py` on the smoke matrix runs clean and keeps only scored rows.
6. sys.csv:
   - the header has 31 columns and every row has 31 fields (`bad_rows 0`);
   - nongame_cores, game_cores and disk_MBps are filled on every row;
   - proc_nongame_cores, nongame_io_MBps and the top lists are filled on rows 0, 5, 10, ...;
   - `proc_fails=0`.
7. The sys-csv start line shows `dll=LdSys-4efd5c91.dll(cached)` and `proc=[every=5 ...]`. The stop line parses and run.json carries `stop_line`.
8. Sampler cost from the stop/timing lines, on an otherwise idle machine:
   - `steady_cpu_pct` <= ~0.5;
   - `skipped=0`;
   - `sample_ms_max` well under the 1000 ms interval (target < 50 ms; > 200 ms on an idle machine means set ProcEvery 0);
   - no `sample_gaps` flag.
9. Frame-time check: in perf.csv, frames > 8 ms must show no 5-second periodicity aligned with the snapshot rows (match sys.csv `epoch_s` of rows 0, 5, 10, ... against frame wall times). Best: one A/B pair on the same bin, ProcEvery 0 vs 5 (temporary local default edit, restored afterwards) with equal median and p99 within noise.
10. `nongame_load` appears only in flags_info, never in flags_excluding. `excluded` is unchanged by it.
11. sys_selftest.ps1 is patched (C2) and passes.

## Read/Sent

Read: everything in the files-rated table, plus run-timing.ps1 L231-245, L495-602; run-night.ps1 L183-213; sys_selftest.ps1 L27, L151, L225; matrix_recheck.py L127-280; load_phase.py L318-350; `staged/test/*/sys.out.txt`; `build/agent8/cache` listing.

Sent to the Overseer on writing.
