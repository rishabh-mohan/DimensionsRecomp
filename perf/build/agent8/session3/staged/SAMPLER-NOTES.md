# Staged: per-process CPU / disk-IO attribution in sys.csv + `nongame_load` info flag

E9.1 for M8, 2026-11-25. STAGED ONLY. Nothing in `bench\agent8\run\` was touched.

Why: the 03:25-03:41 slowdown episode (build/agent8/HANDOFF.md L86-93) hit every arm and no counter explained it.
The quiet gate and valid_timing only look at window start. With this change, sys.csv says who was using CPU and disk
during the window, and sys.json gets an info flag when non-game load is high (W5b hygiene rule: >= 2.8 cores).

## Files

| staged file | replaces (on install) | diff |
|---|---|---|
| `staged\drivers\LdSys.cs` | `bench\agent8\run\drivers\LdSys.cs` | `LdSys.cs.diff` (+215 / -7) |
| `staged\drivers\sys-csv.ps1` | `bench\agent8\run\drivers\sys-csv.ps1` | `sys-csv.ps1.diff` (+18 / -7) |
| `staged\sys_summary.py` | `bench\agent8\run\sys_summary.py` | `sys_summary.py.diff` (+100 / -13) |

Tests and evidence are in `staged\test\`:
- `smoke.ps1`: driver smoke test.
- `cmp_old.py`: equality on old sys.csv files.
- `synthetic.py` with `synthetic-sys.csv`.
- run dirs `smoke-orig`, `smoke`, `smoke3`, `cmp-new1`, `cmp-new5` (this one has `sys.json` from real data), `cmp-orig`.

## sys.csv: 7 new trailing columns (the existing 24 are unchanged in name and order)

| column | rows | meaning |
|---|---|---|
| `nongame_cores` | every row | Machine busy cores minus game cores over the last tick. Busy cores come from `GetSystemTimes`: (kernel+user-idle)/dt, which includes DPC/ISR time. Game cores come from `GetProcessTimes(game)`. O(1). |
| `game_cores` | every row | Game process cores over the last tick. |
| `proc_nongame_cores` | snapshot rows | Sum of per-process CPU deltas, excluding Idle (pid 0) and the game. Usually a little below `nongame_cores` because DPC/ISR time is not charged to processes. In the smoke test: 6.79 vs 6.87. |
| `nongame_io_MBps` | snapshot rows | Read+Write TransferCount delta of all non-game processes, MB/s (MB = 1e6 bytes). This is logical I/O: it includes cache hits, and network I/O too. |
| `disk_MBps` | every row | PDH `\PhysicalDisk(_Total)\Disk Bytes/sec` (physical disk). |
| `top_cpu` | snapshot rows | Top 5 non-game processes by CPU, as `name:pid:cores;...` (3 dp). |
| `top_io` | snapshot rows | Top 3 non-game processes by I/O, as `name:pid:MBps;...` (2 dp). |

Snapshot = one `NtQuerySystemInformation(SystemProcessInformation)` call. It gives CPU times and I/O transfer counts for all
processes in a single call, diffed against the previous snapshot (keyed by pid+create time). Processes created since the
previous snapshot count fully. A snapshot is taken on rows where `Rows % ProcEvery == 0`. On the other rows those 4 cells
are blank.

Process names are cleaned: `:`, `;` and space become `_`. The call is read-only, starts no child processes and uses a
reused buffer (~690 KB for ~330 processes). Machine/game times are baselined in Init, so row 1 already has values.

Example rows from the real data (a sleeper was passed as the game; the actual game was running separately):
```
top_cpu = legodimensions.exe:7284:2.635;MsMpEng.exe:6368:1.607;dwm.exe:1936:0.558;System:4:0.388;agy.exe:21216:0.347
top_io  = SmartByteTelemetry.exe:27192:10.34;svchost.exe:4468:2.44;agy.exe:21216:1.58
```

### Deviation from the brief: default `-ProcEvery 5`, not every tick
The snapshot syscall costs **9.6 ms CPU per call** (mean; max 11-16 ms). That is about 8x the whole original row
(1.1-1.2 ms). It walks all ~330 processes and their threads. Doing it every tick roughly sextuples the sampler's steady CPU
(see the cost table), which conflicts with "must stay cheap". So:
- `nongame_cores`, `game_cores` and `disk_MBps` are on **every** row, from O(1) calls. This is what the flag uses.
- The attribution (top lists) runs every 5th row by default.

`-ProcEvery 1` restores every tick. `-ProcEvery 0` turns snapshots off (the every-row columns stay). **M8 decides.**

## sys-csv.ps1
- New param `-ProcEvery` (string, default `'5'`, 0..3600; a bad value exits 2 like the other params). It sets `[LdSys]::ProcEvery` before `Init`.
- Repo root = the nearest ancestor that holds `build\agent8`, falling back to the old 4-levels-up. This keeps the dll cache at `build\agent8\cache` from both the staged and the installed location. Installed, it resolves to the same path as before.
- Start line gains ` proc=[every=5 procs=330 buf_kb=1024 base_ms=..]` at the end. `counters=` now reads `6/6` (it was 5/5) because of the new disk counter.
- Timing line gains `proc_snaps= proc_fails= procs= proc_sys_ms= proc_sys_cpu_ms=mean/max proc_kb=`.
- **The stop line is unchanged** (run-timing parses it).
- The new LdSys.cs sha compiles a new `build\agent8\cache\LdSys-<sha8>.dll` on first use (~3 s once). The tested final build is `LdSys-4efd5c91.dll`.
- **Never pass `-ProcEvery` to the original driver**: it rejects unknown params.

## sys.json: new keys (sys_summary.py)
- Top level:
  - `nongame_thr` (float, CLI `--nongame-thr`, default 2.8).
  - `file.proc_columns` (bool).
- In both `window` and `run`:
  - `nongame_rows`, `nongame_cores_mean`, `nongame_cores_max`, `nongame_ge_thr_share` (share of rows with nongame_cores >= thr)
  - `game_cores_mean`, `disk_MBps_mean`, `disk_MBps_max`
  - `proc_rows`, `proc_nongame_cores_mean`, `nongame_io_MBps_mean`, `nongame_io_MBps_max`
  - `top_cpu_procs`: `[{proc:"name:pid", core_s, cores_mean, rows}]`, top 5 by summed CPU.
  - `top_io_procs`: `[{proc, MB, MBps_mean, rows}]`, top 5 by summed I/O.
  - Sums weight each snapshot by its interval (time since the previous snapshot row). Only processes that made a row's top list are counted, so these are **lower bounds**.
- **Flag `nongame_load`**: set when `window.nongame_cores_mean >= nongame_thr`.
- The SYS summary line gets a `; nongame X cores (max, >= thr in N% of rows), game, disk, top cpu, top io` suffix only when proc data exists.
- **Old sys.csv files (old header):** every new window/run key is `null`, `proc_columns=false`, no flag, and the summary line is byte-identical. `header_ok` accepts both headers.

## run-timing.ps1: no patch needed
run-timing L592-599: any sys.json flag not in `$sysExcluding` goes to `flags_info`. So `nongame_load` arrives as an
**INFO** flag as-is. Optional patches (M8's call, not applied):
1. Make it excluding (proposal only): add `'nongame_load'` to `$sysExcluding`. The exclusion mechanism is just that list, so no separate category is needed.
2. Threshold passthrough: add a param `[string]$NongameThr = '2.8'` and append `'--nongame-thr', $NongameThr` to the sys_summary call at L513:
   ```
   $ssOut = & python (Join-Path $PSScriptRoot 'sys_summary.py') --csv $sysCsvPath --start-epoch ([string]$mStart.epoch_s) --end-epoch ([string]$mEnd.epoch_s) --out $sysJson --nongame-thr $NongameThr 2>&1 | Out-String
   ```
3. ProcEvery passthrough (only if M8 wants a non-default value): append `'-ProcEvery', $ProcEvery` to the sys-csv `-ArgumentList` (~L230-260). Do this only together with the new driver.

## Selftest (`bench\agent8\run\selftest\sys_selftest.ps1`): needs a one-line update on install
L27 `$Header` is checked exactly (checks a) header-only and e) header exact), so those two checks would FAIL with the new
driver. Patch: append the new columns to `$Header`:
```
...,scheme,overlay,nongame_cores,game_cores,proc_nongame_cores,nongame_io_MBps,disk_MBps,top_cpu,top_io'
```
The g) key checks are a subset check, so they still pass. Nothing calls the selftest automatically (grep: no callers).
Other sys.csv readers (matrix_recheck.py, readout scripts) read by column name, or are old-run scans; the new columns
are trailing.

## Cost (sleeper pid as "game", machine loaded 60-80% by a separate game run + Roblox, so numbers are noisy)

| run | len | steady_cpu_pct | sample_cpu_ms mean/max | loop_cpu_s | cpu_s (stop line) | skipped |
|---|---|---|---|---|---|---|
| original `smoke-orig` | 15 s | 0.158 | 1.11 | 0.109 | 3.297 | 0 |
| original `cmp-orig` | 25 s | 0.215 | 1.24 / 1.83 | 0.156 | 3.594 | 0 |
| staged N=5 `cmp-new5` | 25 s | 0.381 | 3.15 / 11.97 | 0.203 | 3.219 | 0 |
| staged N=5 `smoke3` (incl. compile) | 15 s | 0.694 | - | - | 2.688 | 0 |
| staged N=1 `cmp-new1` | 30 s | 1.291 | ~11 | 0.453 | 3.438 | 0 |
| staged N=1 v1 `smoke` (incl. compile) | 15 s | 1.264 | 12.36 | - | 3.672 | 2 |

- `cpu_s` is dominated by PowerShell startup/Add-Type (~3 s) and varies ±0.4 s from run to run, so it can't separate the variants. Compare `steady_cpu_pct` / `loop_cpu_s`.
- N=5 adds ~0.17 %-points of one core (~1.7 ms CPU/s). N=1 adds ~1.1 %-points (~11 ms/s).
- Snapshot syscall: `proc_sys_cpu_ms` 9.64 mean / 11.25 max, ~10.6 ms wall.
- Under load the snapshot's wall time spiked once to 288 ms (`sample_ms_max` 351 vs 13.6 for the original). The row timestamps (t_s/epoch_s) are taken **before** the snapshot, so only the write is delayed, not the timestamps. A tick is skipped only if the whole row takes longer than the 1 s interval (0 skipped at N=5).

## Tests run
1. **Old files**: `cmp_old.py` ran the original and staged sys_summary.py on `build\agent8\matrix\20261123-0451\runs\{0528-d11t-r6,0526-d11-r6,0524-d11p-r6}` with the run.json window epochs. Result: identical summary line, all original keys identical, the 13 new window/run keys null, `nongame_thr` 2.8, `proc_columns` false. **ALL OK**.
2. **Synthetic** (`synthetic.py`, `synthetic-sys.csv`): window over the load seconds gives flag set, mean 4.0, share 1.0, top MsMpEng 68.0 core_s / 3.4 cores. Whole file gives mean 2.0, no flag. The same with `--nongame-thr 1.5` gives the flag. **ALL OK**.
3. **Driver smoke** (`cmp-new5`, 25 rows): `nongame_cores` 25/25, `game_cores` 25/25, `disk_MBps` 25/25; `proc_nongame_cores` / `nongame_io_MBps` / `top_cpu` / `top_io` 5/5 snapshot rows (rows 1, 6, 11, ...). `proc_fails=0`.
4. **Real-data summary** on `cmp-new5\sys.csv` (window = rows 2..24): nongame 7.42 cores mean (max 13.92, 100% >= 2.8), flags `not_foreground, nongame_load`, top cpu legodimensions.exe 2.53 cores (the actual game, which this test treats as non-game), MsMpEng 0.98; top io SmartByteTelemetry 9.76 MB/s; disk 1.4 MB/s mean (max 4.2). Shows that logical I/O and physical disk differ.

## Install (only when no launcher is pinned to bench\agent8\run, e.g. in daytime)
1. Copy `staged\drivers\LdSys.cs` and `staged\drivers\sys-csv.ps1` to `bench\agent8\run\drivers\`, and `staged\sys_summary.py` to `bench\agent8\run\`. Install all three together. The old summary still parses a new-header file by column name: tested on `cmp-new5`, it gave
   exit 0 and the same flags. But it records `file.header_ok=false` and ignores the new columns. The new summary handles both headers.
2. Update `selftest\sys_selftest.ps1` L27 `$Header` (above), then run the selftest once.
3. Optional run-timing patches 1-3 above.
4. The first run compiles `build\agent8\cache\LdSys-4efd5c91.dll` (it already exists from the tests, so it only loads it).

## Caveats / open
- Default `ProcEvery=5` instead of every tick (above). M8 decides.
- `top_*` and `proc_nongame_cores` miss DPC/ISR time. A process that exits between snapshots loses its last partial interval. Window sums are lower bounds.
- `nongame_io_MBps` / `top_io` are logical process I/O (cache, network, named pipes). `disk_MBps` is physical.
- The stale comment on `ProcInfo` (LdSys.cs L369) says `failed:0x...`, but the code writes `failed`. It was left as-is so the tested sha (4efd5c91) stays valid.
- Extra test dlls in `build\agent8\cache\`: `LdSys-c21dbc8f`, `-75d93666` (intermediate) and `-4efd5c91` (final). Nothing was deleted.
