# Read-only scan: 20261122-1541 (Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; W4b adds d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1)

- matrix dir: <workspace>\build\agent8\matrix\20261122-1541; 17 runs (16 scored, 1 cold); reference arm d0; arms d0, B, d3, d11t
- script: <workspace>\build\agent8\readout\w4b\scan\scan_matrix.py (stdlib, read-only; rules in its docstring); CSVs next to this file: proof.csv, health.csv, slow.csv, bins.csv, warn_types.csv
- Agent 8 inputs compared: timerq build/agent8/readout/w4b/timerq.txt (17 rows of 20261122-1541); rules build/agent8/readout/w4b/rules.md; bins json build/agent8/readout/w4b/w4b.json (17 runs); phase build/agent8/readout/w4b/phase.json

## 1. Proof lines and arm configuration (all runs)

Expected (from matrix.json arms): 1 ms line exactly once where the arm sets host_timer_resolution_ms=1, else 0; precise line exactly once where it sets timer_queue_precise_wait=true, else 0; REX_TIMER_WAIT_BLOCKING=1 in run.json env_set only where the arm has it; params.cvar, args and bin_dir equal to the arm.

| seq | run | arm | kind | bin | cvars n | env_set | 1 ms lines (exp) | precise lines (exp) | deviations |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | d0 | cold | devoff2-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 2 | 1542-d0-r1 | d0 | scored | devoff2-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 3 | 1545-B-r1 | B | scored | devoffB-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 4 | 1547-d3-r1 | d3 | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 5 | 1549-d11t-r1 | d11t | scored | devoff2-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 6 | 1551-B-r2 | B | scored (not timing) | devoffB-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 7 | 1553-d3-r2 | d3 | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 8 | 1556-d11t-r2 | d11t | scored | devoff2-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 9 | 1558-d0-r2 | d0 | scored | devoff2-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 10 | 1600-d3-r3 | d3 | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 11 | 1602-d11t-r3 | d11t | scored | devoff2-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 12 | 1604-d0-r3 | d0 | scored | devoff2-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 13 | 1606-B-r3 | B | scored | devoffB-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 14 | 1608-d11t-r4 | d11t | scored | devoff2-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 15 | 1611-d0-r4 | d0 | scored | devoff2-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 16 | 1613-B-r4 | B | scored | devoffB-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 17 | 1615-d3-r4 | d3 | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |

- proof deviations: none (17 runs)
- vs Agent 8 (timerq ms1/precise/env columns: 0 runs; rules.md R7 per-run lines: 4 runs): all agree
- timer-related log line `Host timer resolution set to 1 ms (background opt-out on)` (normalised `[info] core: Host timer resolution set to # ms (background opt-out on)`): 4 runs (1549-d11t-r1 x1, 1556-d11t-r2 x1, 1602-d11t-r3 x1, 1608-d11t-r4 x1)

## 2. game.log health (all runs)

| seq | run | arm | log files | [error] | [critical] | FATAL | [warning] all | non-INSTALL [warning] | INSTALL .DAT FAILED | other INSTALL warn | STUCK-LOCK | unknown cvar / flag-like | shutdown lines | deviations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | d0 | game.log (94 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 2 | 1542-d0-r1 | d0 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 3 | 1545-B-r1 | B | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 4 | 1547-d3-r1 | d3 | game.log (94 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 5 | 1549-d11t-r1 | d11t | game.log (95 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 6 | 1551-B-r2 | B | game.log (94 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 7 | 1553-d3-r2 | d3 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 8 | 1556-d11t-r2 | d11t | game.log (99 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 9 | 1558-d0-r2 | d0 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 10 | 1600-d3-r3 | d3 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 11 | 1602-d11t-r3 | d11t | game.log (95 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 12 | 1604-d0-r3 | d0 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 13 | 1606-B-r3 | B | game.log (94 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 14 | 1608-d11t-r4 | d11t | game.log (95 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 15 | 1611-d0-r4 | d0 | game.log (94 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 16 | 1613-B-r4 | B | game.log (94 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 17 | 1615-d3-r4 | d3 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |

- health deviations: none

Warning types (normalised; k/n scored runs of the arm that have it, total lines in brackets; cold runs separately):

| warning type | total | d0 | B | d3 | d11t | 1541-cold-d0 (cold) |
|---|---|---|---|---|---|---|
| krnl: IoDismountVolumeByFileHandle(#x#) - stub | 34 | 4/4 runs (8) | 4/4 runs (8) | 4/4 runs (8) | 4/4 runs (8) | 2 |
| krnl: Stub XFileFsDeviceInformation! | 34 | 4/4 runs (8) | 4/4 runs (8) | 4/4 runs (8) | 4/4 runs (8) | 2 |
| krnl: [NtCreateFile] FAILED: path='d:\INSTALL#_#.DAT' -> #x# | 578 | 4/4 runs (136) | 4/4 runs (136) | 4/4 runs (136) | 4/4 runs (136) | 34 |
| krnl: [NtCreateFile] FAILED: path='d:\INSTALL#_#.HDR' -> #x# | 17 | 4/4 runs (4) | 4/4 runs (4) | 4/4 runs (4) | 4/4 runs (4) | 1 |
| krnl: __imp__XamBackgroundDownloadSetMode STUB | 17 | 4/4 runs (4) | 4/4 runs (4) | 4/4 runs (4) | 4/4 runs (4) | 1 |

- types in B (scored) but not in d0 (scored): none
- types in d0 (scored) but not in B (scored): none
- types in d3 (scored) but not in d0 (scored): none
- types in d0 (scored) but not in d3 (scored): none
- types in d11t (scored) but not in d0 (scored): none
- types in d0 (scored) but not in d11t (scored): none
- types in the cold run 1541-cold-d0 but not in d0 (scored): none
- [error]/[critical] types: none

## 3. Slow state (sys.csv from the first frame on; E-cores < 800 MHz for 3+ samples in a row)

| seq | run | arm | onset s: mine / timerq / R3 | run E<800 share %: mine / timerq | in 3+ stretches % | stretches | stretch in window | window E<800 share %: mine / R3 | window rows | win E MHz | win P MHz | win P util % | win E util % | run.json sys.window E/P MHz, P/E util | fg in window % (fg!=1 rows before measure end; fg values from ff) | window fps |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | d0 (cold) | - / - / - | 0 / 0 | 0 | 0 | no | 0 / - | 30 | 1729 | 2051 | 104.0 | 90.3 | 1729.0 / 2051.0 / 104.01 / 90.29 | 100 (0; 0/1) | 325.9 |
| 2 | 1542-d0-r1 | d0 | 93.0 / 93 / 93 | 22 / 22 | 22 | 1 | yes | 35 / 35 | 49 | 1163 | 1894 | 105.9 | 67.8 | 1163.0 / 1894.0 / 105.89 / 67.83 | 100 (0; 0/1) | 256.4 |
| 3 | 1545-B-r1 | B | 94.2 / 94 / 94 | 19 / 19 | 19 | 1 | yes | 32 / 32 | 50 | 1194 | 1877 | 87.1 | 58.0 | 1194.0 / 1877.0 / 87.08 / 57.95 | 100 (0; 0/1) | 317.1 |
| 4 | 1547-d3-r1 | d3 | 75.9 / 76 / 76 | 35 / 35 | 35 | 1 | yes | 70 / 70 | 50 | 830 | 1868 | 99.4 | 46.1 | 830.0 / 1868.0 / 99.4 / 46.06 | 100 (0; 0/1) | 231.0 |
| 5 | 1549-d11t-r1 | d11t | 61.0 / 61 / 61 | 42 / 42 | 42 | 2 | yes | 96 / 96 | 50 | 573 | 1852 | 99.5 | 34.0 | 573.0 / 1852.0 / 99.49 / 33.98 | 100 (0; 0/1) | 206.4 |
| 6 | 1551-B-r2 | B | 0.9 / 1 / 1 | 32 / 32 | 31 | 2 | yes | 64 / 64 | 50 | 767 | 1893 | 102.7 | 45.4 | 767.0 / 1893.0 / 102.72 / 45.44 | 100 (0; 0/1) | 234.5 |
| 7 | 1553-d3-r2 | d3 | 84.0 / 84 / 84 | 26 / 26 | 26 | 1 | yes | 54 / 54 | 50 | 1031 | 1936 | 91.0 | 51.5 | 1031.0 / 1936.0 / 91.05 / 51.48 | 100 (0; 0/1) | 298.6 |
| 8 | 1556-d11t-r2 | d11t | 63.0 / 63 / 63 | 46 / 46 | 46 | 1 | yes | 96 / 96 | 50 | 587 | 1895 | 100.8 | 34.6 | 587.0 / 1895.0 / 100.82 / 34.63 | 100 (0; 0/1) | 220.6 |
| 9 | 1558-d0-r2 | d0 | 72.0 / 72 / 72 | 37 / 37 | 37 | 1 | yes | 76 / 76 | 50 | 804 | 1933 | 94.8 | 43.7 | 804.0 / 1933.0 / 94.76 / 43.7 | 100 (0; 0/1) | 270.4 |
| 10 | 1600-d3-r3 | d3 | 53.7 / 54 / 54 | 52 / 52 | 52 | 1 | yes | 100 / 100 | 48 | 551 | 1883 | 103.3 | 33.3 | 551.0 / 1883.0 / 103.26 / 33.33 | 100 (0; 0/1) | 198.4 |
| 11 | 1602-d11t-r3 | d11t | 1.0 / 1 / 1 | 81 / 81 | 78 | 5 | yes | 96 / 96 | 50 | 612 | 1935 | 91.2 | 35.1 | 612.0 / 1935.0 / 91.16 / 35.13 | 100 (0; 0/1) | 277.2 |
| 12 | 1604-d0-r3 | d0 | 2.0 / 2 / 2 | 90 / 90 | 90 | 4 | yes | 100 / 100 | 50 | 555 | 1905 | 101.0 | 33.2 | 555.0 / 1905.0 / 100.99 / 33.2 | 100 (0; 0/1) | 223.1 |
| 13 | 1606-B-r3 | B | 4.0 / 4 / 4 | 97 / 97 | 97 | 1 | yes | 100 / 100 | 50 | 545 | 1891 | 101.1 | 33.3 | 545.0 / 1891.0 / 101.11 / 33.3 | 100 (0; 0/1) | 230.8 |
| 14 | 1608-d11t-r4 | d11t | 1.0 / 1 / 1 | 85 / 85 | 85 | 2 | yes | 100 / 100 | 49 | 573 | 1911 | 96.0 | 33.5 | 573.0 / 1911.0 / 96.1 / 33.54 | 100 (0; 0/1) | 254.9 |
| 15 | 1611-d0-r4 | d0 | 4.0 / 4 / 4 | 96 / 96 | 96 | 2 | yes | 100 / 100 | 49 | 553 | 1890 | 101.7 | 33.2 | 553.0 / 1890.0 / 101.7 / 33.21 | 100 (0; 0/1) | 213.9 |
| 16 | 1613-B-r4 | B | 3.0 / 3 / 3 | 90 / 90 | 88 | 6 | yes | 90 / 90 | 50 | 638 | 1911 | 92.4 | 35.5 | 638.0 / 1911.0 / 92.41 / 35.5 | 100 (0; 0/1) | 275.8 |
| 17 | 1615-d3-r4 | d3 | 0.9 / 1 / 1 | 93 / 93 | 92 | 6 | yes | 98 / 98 | 50 | 610 | 1940 | 93.1 | 34.0 | 610.0 / 1940.0 / 93.06 / 34.04 | 100 (0; 0/1) | 266.8 |

- scored runs with a 3+ stretch overlapping the window: 16 of 16; onsets (scored) 1-94 s; never slow: 1541-cold-d0
- foreground: window fg share min 100 % over scored runs; rows with fg_game != 1 between the first frame and the measure end: none
- vs Agent 8 (timerq.txt onset rounded to 1 s and run share; rules.md R3 onset and window share): all agree
- window means vs run.json sys.window (tolerance 1 MHz / 0.05 pts): 1608-d11t-r4 p_util_mean 96.03 vs 96.1

## 4. 10 s bins of the scored window (perf.csv frame times; sys.csv rows by interval centre)

### fps per bin (`*` = below 0.85 x the run's median bin; ratio in bins.csv column fps_over_run_median_bin)

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (cold) | 297.0 | 332.6 | 347.9 | - | - |
| 2 | 1542-d0-r1 | 327.9 | 301.4 | 302.6 | 179.3* | 170.8* |
| 3 | 1545-B-r1 | 358.6 | 383.4 | 379.4 | 244.7* | 219.7* |
| 4 | 1547-d3-r1 | 333.3 | 268.6 | 167.0* | 204.5 | 181.5 |
| 5 | 1549-d11t-r1 | 172.0* | 183.5 | 237.1 | 236.2 | 203.2 |
| 6 | 1551-B-r2 | 289.9 | 199.9 | 206.7 | 216.2 | 259.6 |
| 7 | 1553-d3-r2 | 359.3 | 400.5 | 277.6 | 251.5 | 204.3* |
| 8 | 1556-d11t-r2 | 231.9 | 243.0 | 170.5* | 213.4 | 243.9 |
| 9 | 1558-d0-r2 | 373.2 | 258.0 | 246.5 | 270.7 | 204.0* |
| 10 | 1600-d3-r3 | 154.5* | 180.0* | 212.2 | 228.9 | 216.5 |
| 11 | 1602-d11t-r3 | 278.0 | 276.2 | 277.6 | 282.1 | 271.9 |
| 12 | 1604-d0-r3 | 227.3 | 217.8 | 220.3 | 254.1 | 195.8 |
| 13 | 1606-B-r3 | 224.3 | 224.0 | 259.2 | 206.4 | 239.8 |
| 14 | 1608-d11t-r4 | 232.0 | 236.1 | 259.1 | 268.6 | 278.7 |
| 15 | 1611-d0-r4 | 234.8 | 216.7 | 196.4 | 172.4* | 249.3 |
| 16 | 1613-B-r4 | 262.8 | 286.0 | 318.8 | 266.2 | 245.2 |
| 17 | 1615-d3-r4 | 242.5 | 288.4 | 299.5 | 248.6 | 254.9 |

### draws/frame p50 per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (cold) | 226 | 226 | 226 | - | - |
| 2 | 1542-d0-r1 | 226 | 226 | 226 | 226 | 226 |
| 3 | 1545-B-r1 | 226 | 226 | 226 | 226 | 226 |
| 4 | 1547-d3-r1 | 226 | 226 | 226 | 226 | 226 |
| 5 | 1549-d11t-r1 | 226 | 226 | 226 | 226 | 226 |
| 6 | 1551-B-r2 | 226 | 226 | 226 | 226 | 226 |
| 7 | 1553-d3-r2 | 226 | 226 | 226 | 226 | 226 |
| 8 | 1556-d11t-r2 | 226 | 226 | 226 | 226 | 226 |
| 9 | 1558-d0-r2 | 226 | 226 | 226 | 226 | 226 |
| 10 | 1600-d3-r3 | 226 | 226 | 226 | 226 | 226 |
| 11 | 1602-d11t-r3 | 226 | 226 | 226 | 226 | 226 |
| 12 | 1604-d0-r3 | 226 | 226 | 226 | 226 | 226 |
| 13 | 1606-B-r3 | 226 | 226 | 226 | 226 | 226 |
| 14 | 1608-d11t-r4 | 226 | 226 | 226 | 226 | 226 |
| 15 | 1611-d0-r4 | 226 | 226 | 226 | 226 | 226 |
| 16 | 1613-B-r4 | 226 | 226 | 226 | 226 | 226 |
| 17 | 1615-d3-r4 | 226 | 226 | 226 | 226 | 226 |

### E MHz mean per bin (E<800 share %)

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (cold) | 1506 (0) | 1802 (0) | 1883 (0) | - | - |
| 2 | 1542-d0-r1 | 1518 (0) | 1502 (0) | 1508 (0) | 675 (80) | 554 (100) |
| 3 | 1545-B-r1 | 1501 (0) | 1484 (0) | 1494 (0) | 846 (70) | 548 (100) |
| 4 | 1547-d3-r1 | 1512 (0) | 985 (50) | 554 (100) | 546 (100) | 554 (100) |
| 5 | 1549-d11t-r1 | 560 (100) | 557 (100) | 554 (100) | 615 (80) | 577 (100) |
| 6 | 1551-B-r2 | 1241 (30) | 554 (100) | 556 (100) | 576 (90) | 909 (0) |
| 7 | 1553-d3-r2 | 1648 (0) | 1561 (0) | 836 (70) | 560 (100) | 550 (100) |
| 8 | 1556-d11t-r2 | 727 (80) | 557 (100) | 553 (100) | 553 (100) | 546 (100) |
| 9 | 1558-d0-r2 | 1535 (0) | 646 (90) | 547 (100) | 639 (100) | 558 (100) |
| 10 | 1600-d3-r3 | 557 (100) | 548 (100) | 544 (100) | 551 (100) | 556 (100) |
| 11 | 1602-d11t-r3 | 637 (100) | 603 (100) | 607 (90) | 601 (100) | 617 (90) |
| 12 | 1604-d0-r3 | 565 (100) | 560 (100) | 554 (100) | 544 (100) | 550 (100) |
| 13 | 1606-B-r3 | 544 (100) | 536 (100) | 550 (100) | 549 (100) | 546 (100) |
| 14 | 1608-d11t-r4 | 555 (100) | 548 (100) | 557 (100) | 583 (100) | 622 (100) |
| 15 | 1611-d0-r4 | 551 (100) | 554 (100) | 557 (100) | 555 (100) | 548 (100) |
| 16 | 1613-B-r4 | 610 (100) | 636 (100) | 753 (60) | 639 (90) | 554 (100) |
| 17 | 1615-d3-r4 | 559 (100) | 673 (90) | 686 (100) | 576 (100) | 556 (100) |

### P util % mean per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (cold) | 108.5 | 102.0 | 97.6 | - | - |
| 2 | 1542-d0-r1 | 98.1 | 113.6 | 112.6 | 102.2 | 103.1 |
| 3 | 1545-B-r1 | 86.3 | 78.2 | 80.7 | 95.3 | 96.6 |
| 4 | 1547-d3-r1 | 96.1 | 92.1 | 101.7 | 102.3 | 104.8 |
| 5 | 1549-d11t-r1 | 99.9 | 101.8 | 99.2 | 96.6 | 99.9 |
| 6 | 1551-B-r2 | 101.4 | 99.3 | 101.8 | 103.4 | 107.7 |
| 7 | 1553-d3-r2 | 86.8 | 75.3 | 95.2 | 96.3 | 101.7 |
| 8 | 1556-d11t-r2 | 97.1 | 97.1 | 105.2 | 103.7 | 101.0 |
| 9 | 1558-d0-r2 | 83.4 | 96.6 | 95.3 | 94.1 | 104.8 |
| 10 | 1600-d3-r3 | 104.9 | 104.5 | 102.6 | 101.8 | 102.4 |
| 11 | 1602-d11t-r3 | 89.8 | 91.5 | 90.7 | 91.2 | 91.8 |
| 12 | 1604-d0-r3 | 101.4 | 101.6 | 101.0 | 98.0 | 103.0 |
| 13 | 1606-B-r3 | 101.6 | 101.9 | 99.1 | 102.4 | 100.5 |
| 14 | 1608-d11t-r4 | 100.3 | 99.2 | 96.0 | 93.0 | 91.7 |
| 15 | 1611-d0-r4 | 100.2 | 102.4 | 102.7 | 104.2 | 99.0 |
| 16 | 1613-B-r4 | 94.1 | 92.6 | 84.2 | 95.0 | 96.2 |
| 17 | 1615-d3-r4 | 97.0 | 88.9 | 86.7 | 97.8 | 94.8 |

### P MHz mean per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (cold) | 1904 | 2087 | 2148 | - | - |
| 2 | 1542-d0-r1 | 1946 | 1946 | 1946 | 1803 | 1825 |
| 3 | 1545-B-r1 | 1907 | 1909 | 1913 | 1821 | 1827 |
| 4 | 1547-d3-r1 | 1921 | 1886 | 1799 | 1863 | 1868 |
| 5 | 1549-d11t-r1 | 1770 | 1820 | 1887 | 1906 | 1877 |
| 6 | 1551-B-r2 | 1924 | 1839 | 1866 | 1900 | 1936 |
| 7 | 1553-d3-r2 | 2037 | 1945 | 1897 | 1924 | 1879 |
| 8 | 1556-d11t-r2 | 1862 | 1895 | 1885 | 1907 | 1928 |
| 9 | 1558-d0-r2 | 1945 | 1916 | 1944 | 1945 | 1910 |
| 10 | 1600-d3-r3 | 1840 | 1879 | 1894 | 1902 | 1903 |
| 11 | 1602-d11t-r3 | 1936 | 1930 | 1935 | 1937 | 1936 |
| 12 | 1604-d0-r3 | 1945 | 1886 | 1882 | 1924 | 1887 |
| 13 | 1606-B-r3 | 1886 | 1894 | 1909 | 1877 | 1889 |
| 14 | 1608-d11t-r4 | 1891 | 1888 | 1922 | 1929 | 1927 |
| 15 | 1611-d0-r4 | 1945 | 1887 | 1870 | 1851 | 1897 |
| 16 | 1613-B-r4 | 1920 | 1914 | 1908 | 1914 | 1901 |
| 17 | 1615-d3-r4 | 1945 | 1945 | 1945 | 1920 | 1945 |

### E util % mean per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (cold) | 89.2 | 92.9 | 86.9 | - | - |
| 2 | 1542-d0-r1 | 81.9 | 90.0 | 90.0 | 40.5 | 33.3 |
| 3 | 1545-B-r1 | 73.7 | 65.8 | 66.6 | 46.3 | 32.8 |
| 4 | 1547-d3-r1 | 80.0 | 50.3 | 33.3 | 33.3 | 33.3 |
| 5 | 1549-d11t-r1 | 33.8 | 33.3 | 33.1 | 35.6 | 34.1 |
| 6 | 1551-B-r2 | 71.1 | 33.0 | 33.3 | 35.1 | 54.7 |
| 7 | 1553-d3-r2 | 78.0 | 67.8 | 45.9 | 32.4 | 33.3 |
| 8 | 1556-d11t-r2 | 40.2 | 33.1 | 33.2 | 33.3 | 33.3 |
| 9 | 1558-d0-r2 | 74.1 | 37.1 | 32.2 | 36.2 | 33.5 |
| 10 | 1600-d3-r3 | 33.3 | 33.3 | 33.3 | 33.3 | 33.3 |
| 11 | 1602-d11t-r3 | 36.2 | 34.8 | 34.6 | 35.1 | 35.0 |
| 12 | 1604-d0-r3 | 33.2 | 33.3 | 33.3 | 32.9 | 33.3 |
| 13 | 1606-B-r3 | 33.3 | 33.3 | 33.2 | 33.3 | 33.3 |
| 14 | 1608-d11t-r4 | 33.3 | 33.3 | 32.8 | 33.3 | 35.2 |
| 15 | 1611-d0-r4 | 32.9 | 33.3 | 33.3 | 33.3 | 33.2 |
| 16 | 1613-B-r4 | 34.7 | 36.1 | 38.7 | 35.8 | 32.2 |
| 17 | 1615-d3-r4 | 32.6 | 35.7 | 36.3 | 33.7 | 31.9 |

Slow bins (scored runs):

| run | bin | fps | x run median bin | E MHz | E<800 share % | P util % | P MHz | E util % | E mean < 800 | P util >= 90 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1542-d0-r1 | 30-40 s | 179.3 | 0.59 | 675 | 80 | 102.2 | 1803 | 40.5 | yes | yes |
| 1542-d0-r1 | 40-50 s | 170.8 | 0.57 | 554 | 100 | 103.1 | 1825 | 33.3 | yes | yes |
| 1545-B-r1 | 30-40 s | 244.7 | 0.68 | 846 | 70 | 95.3 | 1821 | 46.3 | no | yes |
| 1545-B-r1 | 40-50 s | 219.7 | 0.61 | 548 | 100 | 96.6 | 1827 | 32.8 | yes | yes |
| 1547-d3-r1 | 20-30 s | 167.0 | 0.82 | 554 | 100 | 101.7 | 1799 | 33.3 | yes | yes |
| 1549-d11t-r1 | 0-10 s | 172.0 | 0.85 | 560 | 100 | 99.9 | 1770 | 33.8 | yes | yes |
| 1553-d3-r2 | 40-50 s | 204.3 | 0.74 | 550 | 100 | 101.7 | 1879 | 33.3 | yes | yes |
| 1556-d11t-r2 | 20-30 s | 170.5 | 0.74 | 553 | 100 | 105.2 | 1885 | 33.2 | yes | yes |
| 1558-d0-r2 | 40-50 s | 204.0 | 0.79 | 558 | 100 | 104.8 | 1910 | 33.5 | yes | yes |
| 1600-d3-r3 | 0-10 s | 154.5 | 0.73 | 557 | 100 | 104.9 | 1840 | 33.3 | yes | yes |
| 1600-d3-r3 | 10-20 s | 180.0 | 0.85 | 548 | 100 | 104.5 | 1879 | 33.3 | yes | yes |
| 1611-d0-r4 | 30-40 s | 172.4 | 0.80 | 555 | 100 | 104.2 | 1851 | 33.3 | yes | yes |

- bins of scored runs: 80; slow: 12 in 9 runs (1542-d0-r1, 1545-B-r1, 1547-d3-r1, 1549-d11t-r1, 1553-d3-r2, 1556-d11t-r2, 1558-d0-r2, 1600-d3-r3, 1611-d0-r4)
- slow bins (n=12): E mean < 800 in 11; E<800 share >= 50% in 12; P util >= 90 in 12; both E<800 and P>=90 in 11; neither in 0
- other bins (n=68): E mean < 800 in 54; E<800 share >= 50% in 56; P util >= 90 in 58; both E<800 and P>=90 in 50; neither in 6
  - 1542-d0-r1: slow bins E 615 MHz / P util 102.6 vs other bins E 1509 / P util 108.1
  - 1545-B-r1: slow bins E 697 MHz / P util 95.9 vs other bins E 1493 / P util 81.7
  - 1547-d3-r1: slow bins E 554 MHz / P util 101.7 vs other bins E 899 / P util 98.8
  - 1549-d11t-r1: slow bins E 560 MHz / P util 99.9 vs other bins E 576 / P util 99.4
  - 1553-d3-r2: slow bins E 550 MHz / P util 101.7 vs other bins E 1151 / P util 88.4
  - 1556-d11t-r2: slow bins E 553 MHz / P util 105.2 vs other bins E 596 / P util 99.7
  - 1558-d0-r2: slow bins E 558 MHz / P util 104.8 vs other bins E 842 / P util 92.3
  - 1600-d3-r3: slow bins E 553 MHz / P util 104.7 vs other bins E 550 / P util 102.3
  - 1611-d0-r4: slow bins E 555 MHz / P util 104.2 vs other bins E 552 / P util 101.1
- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin E MHz mean: n=80 rho=0.41 (perm p 0.000)
- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin E<800 share: n=80 rho=-0.43 (perm p 0.000)
- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin P util mean: n=80 rho=-0.47 (perm p 0.000)
- my bin fps vs Agent 8's w4b.json stat_bins: 83 bins compared, max |diff| 0.000 fps
- Agent 8's phase.json slow_bins_s: empty for all 17 runs (its criterion differs from the 0.85 x median rule here)
- window fps/frames from perf.csv vs frames.json: all 17 runs agree

## 5. Spearman rank correlations across scored runs (window fps = frames / summed frame time)

| run set | fps vs | n | rho | perm p (two-sided) |
|---|---|---|---|---|
| scored | (a) window E<800 share | 16 | -0.623 | 0.0131 |
| scored | (b) window mean e_eff_mhz | 16 | 0.732 | 0.0023 |
| scored | (c) window mean p_util_pct | 16 | -0.762 | 0.0012 |
| scored | (d) run order (seq) | 16 | -0.074 | 0.7907 |
| scored | extra: window mean p_eff_mhz | 16 | 0.568 | 0.0238 |
| scored | extra: window mean e_util_pct | 16 | 0.671 | 0.0060 |
| scored | extra: onset s (never = 999) | 16 | 0.156 | 0.5617 |
| scored, valid timing only | (a) window E<800 share | 15 | -0.653 | 0.0102 |
| scored, valid timing only | (b) window mean e_eff_mhz | 15 | 0.757 | 0.0018 |
| scored, valid timing only | (c) window mean p_util_pct | 15 | -0.818 | 0.0007 |
| scored, valid timing only | (d) run order (seq) | 15 | -0.096 | 0.7297 |
| scored, valid timing only | extra: window mean p_eff_mhz | 15 | 0.554 | 0.0343 |
| scored, valid timing only | extra: window mean e_util_pct | 15 | 0.700 | 0.0059 |
| scored, valid timing only | extra: onset s (never = 999) | 15 | 0.175 | 0.5257 |

Scored runs by window fps (ascending):

| run | arm | seq | fps | win E<800 % | win E MHz | win P util % | win P MHz | run.json E MHz | run.json P util % | onset s |
|---|---|---|---|---|---|---|---|---|---|---|
| 1600-d3-r3 | d3 | 10 | 198.4 | 100 | 551 | 103.3 | 1883 | 551.0 | 103.26 | 54 |
| 1549-d11t-r1 | d11t | 5 | 206.4 | 96 | 573 | 99.5 | 1852 | 573.0 | 99.49 | 61 |
| 1611-d0-r4 | d0 | 15 | 213.9 | 100 | 553 | 101.7 | 1890 | 553.0 | 101.7 | 4 |
| 1556-d11t-r2 | d11t | 8 | 220.6 | 96 | 587 | 100.8 | 1895 | 587.0 | 100.82 | 63 |
| 1604-d0-r3 | d0 | 12 | 223.1 | 100 | 555 | 101.0 | 1905 | 555.0 | 100.99 | 2 |
| 1606-B-r3 | B | 13 | 230.8 | 100 | 545 | 101.1 | 1891 | 545.0 | 101.11 | 4 |
| 1547-d3-r1 | d3 | 4 | 231.0 | 70 | 830 | 99.4 | 1868 | 830.0 | 99.4 | 76 |
| 1551-B-r2 | B | 6 | 234.5 | 64 | 767 | 102.7 | 1893 | 767.0 | 102.72 | 1 |
| 1608-d11t-r4 | d11t | 14 | 254.9 | 100 | 573 | 96.0 | 1911 | 573.0 | 96.1 | 1 |
| 1542-d0-r1 | d0 | 2 | 256.4 | 35 | 1163 | 105.9 | 1894 | 1163.0 | 105.89 | 93 |
| 1615-d3-r4 | d3 | 17 | 266.8 | 98 | 610 | 93.1 | 1940 | 610.0 | 93.06 | 1 |
| 1558-d0-r2 | d0 | 9 | 270.4 | 76 | 804 | 94.8 | 1933 | 804.0 | 94.76 | 72 |
| 1613-B-r4 | B | 16 | 275.8 | 90 | 638 | 92.4 | 1911 | 638.0 | 92.41 | 3 |
| 1602-d11t-r3 | d11t | 11 | 277.2 | 96 | 612 | 91.2 | 1935 | 612.0 | 91.16 | 1 |
| 1553-d3-r2 | d3 | 7 | 298.6 | 54 | 1031 | 91.0 | 1936 | 1031.0 | 91.05 | 84 |
| 1545-B-r1 | B | 3 | 317.1 | 32 | 1194 | 87.1 | 1877 | 1194.0 | 87.08 | 94 |


## 7. Notes added after the script run (helper, 19:53)

- Log line types across runs (log_types.txt next to this file, made by build\agent8\readout\w5\scan\log_types.py; same normalisation, Toypad payload bytes collapsed): besides the 1 ms line (d11t 1/1/1/1, all other runs 0), the only lines whose count differs between runs are the `Toypad[Read ]` / `Toypad[Write]` exchanges (8 or 10 each per run, Read = Write in every run: cold 8; d0 10/10/10/8; B 10/8/8/8; d3 8/10/10/10; d11t 8/10/8/8). That explains the 94-99 line counts. The other 43 line types have the same count in all 17 runs.
- The 1 ms line is `[info] [core] Host timer resolution set to 1 ms (background opt-out on)`. No other timer-related line in any run (no TimerQueue mode line, nothing naming REX_TIMER_WAIT_BLOCKING), so the blocking mode is visible only in run.json (env_set / params.env).
- Slow-bin rule limits: the 0.85 x own-median rule only flags changes inside a run. Runs in the slow state for the whole window (1600, 1604, 1606, 1608, 1611, 1549, 1556) have their median bin at the slow level, so few or no bins get flagged. Two flags are borderline: 1549 0-10 s (ratio 0.846) and 1600 10-20 s (0.848).
- Window means vs run.json sys.window: one difference, 1608-d11t-r4 P util 96.03 % here (49 window rows) vs 96.1 in run.json. Every other run agrees within 1 MHz / 0.05 pts.
- Onsets by time: runs 2-10 (15:42-16:00) have onsets of 54-94 s, except 1551-B-r2 at 1 s. Every run from 1602 (16:02) on has an onset of 1-4 s and a run E<800 share of 81-97 %.
