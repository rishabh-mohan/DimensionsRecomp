# Read-only scan: 20261122-1756 (Window 5, S3d line (Agent 8's task #10 draft, promoted by Agent 1 at 16:42 after W4b): S4 baseline + timer modes. base = devoff3 (S3d); s0, d11, d11t, d11p = devoff4 (S4a))

- matrix dir: <workspace>\build\agent8\matrix\20261122-1756; 16 runs (15 scored, 1 cold); reference arm base; arms base, s0, d11, d11t, d11p
- script: <workspace>\build\agent8\readout\w4b\scan\scan_matrix.py (stdlib, read-only; rules in its docstring); CSVs next to this file: proof.csv, health.csv, slow.csv, bins.csv, warn_types.csv
- Agent 8 inputs compared: timerq build/agent8/readout/w5/timerq3.txt (16 rows of 20261122-1756); rules build/agent8/readout/w5/rules.md; bins json build/agent8/readout/w5/w5.json (16 runs); phase build/agent8/readout/w5/phase.json

## 1. Proof lines and arm configuration (all runs)

Expected (from matrix.json arms): 1 ms line exactly once where the arm sets host_timer_resolution_ms=1, else 0; precise line exactly once where it sets timer_queue_precise_wait=true, else 0; REX_TIMER_WAIT_BLOCKING=1 in run.json env_set only where the arm has it; params.cvar, args and bin_dir equal to the arm.

| seq | run | arm | kind | bin | cvars n | env_set | 1 ms lines (exp) | precise lines (exp) | deviations |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1756-cold-base | base | cold | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 2 | 1757-base-r1 | base | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 3 | 1800-s0-r1 | s0 | scored | devoff4-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 4 | 1802-d11-r1 | d11 | scored | devoff4-bin ok | 9 ok | - | 1 (1) | 0 (0) | none |
| 5 | 1804-d11t-r1 | d11t | scored | devoff4-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 6 | 1806-d11p-r1 | d11p | scored | devoff4-bin ok | 10 ok | - | 1 (1) | 1 (1) | none |
| 7 | 1808-s0-r2 | s0 | scored | devoff4-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 8 | 1810-d11-r2 | d11 | scored | devoff4-bin ok | 9 ok | - | 1 (1) | 0 (0) | none |
| 9 | 1813-d11t-r2 | d11t | scored | devoff4-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 10 | 1815-d11p-r2 | d11p | scored | devoff4-bin ok | 10 ok | - | 1 (1) | 1 (1) | none |
| 11 | 1817-base-r2 | base | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 12 | 1819-d11-r3 | d11 | scored | devoff4-bin ok | 9 ok | - | 1 (1) | 0 (0) | none |
| 13 | 1821-d11t-r3 | d11t | scored | devoff4-bin ok | 9 ok | REX_TIMER_WAIT_BLOCKING=1 | 1 (1) | 0 (0) | none |
| 14 | 1823-d11p-r3 | d11p | scored | devoff4-bin ok | 10 ok | - | 1 (1) | 1 (1) | none |
| 15 | 1825-base-r3 | base | scored | devoff3-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |
| 16 | 1827-s0-r3 | s0 | scored | devoff4-bin ok | 1 ok | - | 0 (0) | 0 (0) | none |

- proof deviations: none (16 runs)
- vs Agent 8 (timerq ms1/precise/env columns: 16 runs; rules.md R7 per-run lines: 16 runs): all agree
- timer-related log line `Host timer resolution set to 1 ms (background opt-out on)` (normalised `[info] core: Host timer resolution set to # ms (background opt-out on)`): 9 runs (1802-d11-r1 x1, 1804-d11t-r1 x1, 1806-d11p-r1 x1, 1810-d11-r2 x1, 1813-d11t-r2 x1, 1815-d11p-r2 x1, 1819-d11-r3 x1, 1821-d11t-r3 x1, 1823-d11p-r3 x1)
- timer-related log line `TimerQueue: precise wait (timer_queue_precise_wait)` (normalised `[info] core: TimerQueue: precise wait (timer_queue_precise_wait)`): 3 runs (1806-d11p-r1 x1, 1815-d11p-r2 x1, 1823-d11p-r3 x1)

## 2. game.log health (all runs)

| seq | run | arm | log files | [error] | [critical] | FATAL | [warning] all | non-INSTALL [warning] | INSTALL .DAT FAILED | other INSTALL warn | STUCK-LOCK | unknown cvar / flag-like | shutdown lines | deviations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1756-cold-base | base | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 2 | 1757-base-r1 | base | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 3 | 1800-s0-r1 | s0 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 4 | 1802-d11-r1 | d11 | game.log (99 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 5 | 1804-d11t-r1 | d11t | game.log (103 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 6 | 1806-d11p-r1 | d11p | game.log (100 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 7 | 1808-s0-r2 | s0 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 8 | 1810-d11-r2 | d11 | game.log (99 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 9 | 1813-d11t-r2 | d11t | game.log (103 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 10 | 1815-d11p-r2 | d11p | game.log (100 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 11 | 1817-base-r2 | base | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 12 | 1819-d11-r3 | d11 | game.log (99 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 13 | 1821-d11t-r3 | d11t | game.log (95 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 14 | 1823-d11p-r3 | d11p | game.log (100 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 15 | 1825-base-r3 | base | game.log (102 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |
| 16 | 1827-s0-r3 | s0 | game.log (98 lines) | 0 | 0 | 0 | 40 | 5 | 34 (runner 34) | 1 | 0 | 0 / 0 | ok | none |

- health deviations: none

Warning types (normalised; k/n scored runs of the arm that have it, total lines in brackets; cold runs separately):

| warning type | total | base | s0 | d11 | d11t | d11p | 1756-cold-base (cold) |
|---|---|---|---|---|---|---|---|
| krnl: IoDismountVolumeByFileHandle(#x#) - stub | 32 | 3/3 runs (6) | 3/3 runs (6) | 3/3 runs (6) | 3/3 runs (6) | 3/3 runs (6) | 2 |
| krnl: Stub XFileFsDeviceInformation! | 32 | 3/3 runs (6) | 3/3 runs (6) | 3/3 runs (6) | 3/3 runs (6) | 3/3 runs (6) | 2 |
| krnl: [NtCreateFile] FAILED: path='d:\INSTALL#_#.DAT' -> #x# | 544 | 3/3 runs (102) | 3/3 runs (102) | 3/3 runs (102) | 3/3 runs (102) | 3/3 runs (102) | 34 |
| krnl: [NtCreateFile] FAILED: path='d:\INSTALL#_#.HDR' -> #x# | 16 | 3/3 runs (3) | 3/3 runs (3) | 3/3 runs (3) | 3/3 runs (3) | 3/3 runs (3) | 1 |
| krnl: __imp__XamBackgroundDownloadSetMode STUB | 16 | 3/3 runs (3) | 3/3 runs (3) | 3/3 runs (3) | 3/3 runs (3) | 3/3 runs (3) | 1 |

- types in s0 (scored) but not in base (scored): none
- types in base (scored) but not in s0 (scored): none
- types in d11 (scored) but not in base (scored): none
- types in base (scored) but not in d11 (scored): none
- types in d11t (scored) but not in base (scored): none
- types in base (scored) but not in d11t (scored): none
- types in d11p (scored) but not in base (scored): none
- types in base (scored) but not in d11p (scored): none
- types in the cold run 1756-cold-base but not in base (scored): none
- types in the timer arms d11/d11t/d11p (scored) but not in s0 (scored): none
- types in s0 (scored) but not in any timer arm (scored): none
- [error]/[critical] types: none

## 3. Slow state (sys.csv from the first frame on; E-cores < 800 MHz for 3+ samples in a row)

| seq | run | arm | onset s: mine / timerq / R3 | run E<800 share %: mine / timerq | in 3+ stretches % | stretches | stretch in window | window E<800 share %: mine / R3 | window rows | win E MHz | win P MHz | win P util % | win E util % | run.json sys.window E/P MHz, P/E util | fg in window % (fg!=1 rows before measure end; fg values from ff) | window fps |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1756-cold-base | base (cold) | - / - / - | 0 / 0 | 0 | 0 | no | 0 / - | 30 | 1683 | 2052 | 77.4 | 70.9 | 1683.0 / 2052.0 / 77.44 / 70.91 | 100 (0; 0/1) | 395.8 |
| 2 | 1757-base-r1 | base | 87.0 / 87 / 87 | 13 / 13 | 7 | 1 | yes | 26 / 26 | 50 | 1174 | 1931 | 73.3 | 51.3 | 1174.0 / 1931.0 / 73.32 / 51.31 | 100 (0; 0/1) | 384.6 |
| 3 | 1800-s0-r1 | s0 | 39.9 / 40 / 40 | 50 / 50 | 46 | 3 | yes | 68 / 68 | 50 | 725 | 1923 | 86.4 | 40.8 | 725.0 / 1923.0 / 86.44 / 40.77 | 100 (0; 0/1) | 333.4 |
| 4 | 1802-d11-r1 | d11 | 6.0 / 6 / 6 | 68 / 68 | 61 | 8 | yes | 86 / 86 | 50 | 719 | 1945 | 84.3 | 39.9 | 719.0 / 1945.0 / 84.27 / 39.89 | 100 (0; 0/1) | 350.3 |
| 5 | 1804-d11t-r1 | d11t | 13.0 / 13 / 13 | 66 / 66 | 60 | 7 | yes | 94 / 94 | 50 | 676 | 1941 | 82.6 | 37.3 | 676.0 / 1941.0 / 82.61 / 37.33 | 100 (0; 0/1) | 338.5 |
| 6 | 1806-d11p-r1 | d11p | 3.0 / 3 / 3 | 71 / 71 | 69 | 7 | yes | 88 / 88 | 51 | 659 | 1939 | 82.4 | 35.8 | 659.0 / 1939.0 / 82.41 / 35.84 | 100 (0; 0/1) | 343.3 |
| 7 | 1808-s0-r2 | s0 | 21.0 / 21 / 21 | 69 / 69 | 66 | 5 | yes | 94 / 94 | 50 | 597 | 1938 | 91.5 | 34.2 | 597.0 / 1938.0 / 91.49 / 34.18 | 100 (0; 0/1) | 309.9 |
| 8 | 1810-d11-r2 | d11 | 35.0 / 35 / 35 | 58 / 58 | 49 | 7 | yes | 86 / 86 | 50 | 699 | 1929 | 80.9 | 37.4 | 699.0 / 1929.0 / 80.91 / 37.43 | 100 (0; 0/1) | 351.3 |
| 9 | 1813-d11t-r2 | d11t | 1.1 / 1 / 1 | 62 / 62 | 56 | 8 | yes | 76 / 76 | 50 | 729 | 1938 | 76.4 | 36.8 | 729.0 / 1938.0 / 76.37 / 36.81 | 100 (0; 0/1) | 358.7 |
| 10 | 1815-d11p-r2 | d11p | 1.9 / 2 / 2 | 70 / 70 | 63 | 9 | yes | 94 / 94 | 50 | 684 | 1937 | 76.8 | 35.5 | 684.0 / 1937.0 / 76.78 / 35.49 | 100 (0; 0/1) | 356.9 |
| 11 | 1817-base-r2 | base | 3.9 / 4 / 4 | 78 / 78 | 76 | 5 | yes | 100 / 100 | 50 | 554 | 1931 | 98.5 | 33.9 | 554.0 / 1931.0 / 98.5 / 33.87 | 100 (0; 0/1) | 289.2 |
| 12 | 1819-d11-r3 | d11 | 2.0 / 2 / 2 | 70 / 70 | 65 | 9 | yes | 76 / 76 | 50 | 725 | 1924 | 80.0 | 38.4 | 725.0 / 1924.0 / 79.96 / 38.36 | 100 (0; 0/1) | 352.5 |
| 13 | 1821-d11t-r3 | d11t | 4.0 / 4 / 4 | 96 / 96 | 96 | 2 | yes | 100 / 100 | 50 | 551 | 1923 | 91.4 | 32.4 | 551.0 / 1923.0 / 91.38 / 32.44 | 100 (0; 0/1) | 277.1 |
| 14 | 1823-d11p-r3 | d11p | 2.0 / 2 / 2 | 80 / 80 | 71 | 6 | yes | 96 / 96 | 50 | 609 | 1940 | 83.8 | 34.1 | 609.0 / 1940.0 / 83.85 / 34.15 | 100 (0; 0/1) | 335.3 |
| 15 | 1825-base-r3 | base | 22.0 / 22 / 22 | 60 / 60 | 49 | 11 | yes | 72 / 72 | 50 | 740 | 1920 | 79.4 | 38.9 | 740.0 / 1920.0 / 79.36 / 38.92 | 100 (0; 0/1) | 355.6 |
| 16 | 1827-s0-r3 | s0 | 1.9 / 2 / 2 | 62 / 62 | 50 | 8 | yes | 74 / 74 | 50 | 749 | 1924 | 77.9 | 39.1 | 749.0 / 1924.0 / 77.88 / 39.13 | 100 (0; 0/1) | 360.0 |

- scored runs with a 3+ stretch overlapping the window: 15 of 15; onsets (scored) 1-87 s; never slow: 1756-cold-base
- foreground: window fg share min 100 % over scored runs; rows with fg_game != 1 between the first frame and the measure end: none
- vs Agent 8 (timerq.txt onset rounded to 1 s and run share; rules.md R3 onset and window share): all agree
- window means vs run.json sys.window (tolerance 1 MHz / 0.05 pts): all agree

## 4. 10 s bins of the scored window (perf.csv frame times; sys.csv rows by interval centre)

### fps per bin (`*` = below 0.85 x the run's median bin; ratio in bins.csv column fps_over_run_median_bin)

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (cold) | 390.2 | 404.3 | 393.0 | - | - |
| 2 | 1757-base-r1 | 399.5 | 422.5 | 374.7 | 354.0 | 372.3 |
| 3 | 1800-s0-r1 | 284.9* | 335.9 | 361.6 | 365.0 | 319.5 |
| 4 | 1802-d11-r1 | 325.2 | 361.7 | 343.3 | 358.4 | 363.0 |
| 5 | 1804-d11t-r1 | 296.4* | 362.5 | 361.9 | 303.7* | 367.8 |
| 6 | 1806-d11p-r1 | 328.7 | 339.4 | 322.0 | 357.9 | 368.8 |
| 7 | 1808-s0-r2 | 306.7 | 304.9 | 338.6 | 337.6 | 261.7 |
| 8 | 1810-d11-r2 | 325.3 | 368.6 | 342.6 | 368.9 | 351.2 |
| 9 | 1813-d11t-r2 | 287.2* | 383.7 | 373.2 | 375.9 | 373.7 |
| 10 | 1815-d11p-r2 | 330.8 | 364.5 | 347.1 | 373.8 | 368.5 |
| 11 | 1817-base-r2 | 273.8 | 280.9 | 299.1 | 281.3 | 311.0 |
| 12 | 1819-d11-r3 | 354.2 | 338.7 | 353.0 | 342.1 | 374.3 |
| 13 | 1821-d11t-r3 | 258.2 | 278.9 | 270.7 | 257.6 | 320.2 |
| 14 | 1823-d11p-r3 | 293.7 | 327.6 | 337.8 | 366.9 | 350.7 |
| 15 | 1825-base-r3 | 332.5 | 366.2 | 355.2 | 352.1 | 371.8 |
| 16 | 1827-s0-r3 | 341.2 | 374.8 | 372.3 | 339.1 | 372.6 |

### draws/frame p50 per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (cold) | 226 | 226 | 226 | - | - |
| 2 | 1757-base-r1 | 226 | 226 | 226 | 226 | 226 |
| 3 | 1800-s0-r1 | 226 | 226 | 226 | 226 | 226 |
| 4 | 1802-d11-r1 | 226 | 226 | 226 | 226 | 226 |
| 5 | 1804-d11t-r1 | 226 | 226 | 226 | 226 | 226 |
| 6 | 1806-d11p-r1 | 226 | 226 | 226 | 226 | 226 |
| 7 | 1808-s0-r2 | 226 | 226 | 226 | 226 | 226 |
| 8 | 1810-d11-r2 | 226 | 226 | 226 | 226 | 226 |
| 9 | 1813-d11t-r2 | 226 | 226 | 226 | 226 | 226 |
| 10 | 1815-d11p-r2 | 226 | 226 | 226 | 226 | 226 |
| 11 | 1817-base-r2 | 226 | 226 | 226 | 226 | 226 |
| 12 | 1819-d11-r3 | 226 | 226 | 226 | 226 | 226 |
| 13 | 1821-d11t-r3 | 226 | 226 | 226 | 226 | 226 |
| 14 | 1823-d11p-r3 | 226 | 226 | 226 | 226 | 226 |
| 15 | 1825-base-r3 | 226 | 226 | 226 | 226 | 226 |
| 16 | 1827-s0-r3 | 226 | 226 | 226 | 226 | 226 |

### E MHz mean per bin (E<800 share %)

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (cold) | 1749 (0) | 1785 (0) | 1514 (0) | - | - |
| 2 | 1757-base-r1 | 1543 (0) | 1561 (0) | 1151 (40) | 744 (67) | 749 (67) |
| 3 | 1800-s0-r1 | 581 (100) | 700 (100) | 826 (30) | 838 (20) | 679 (90) |
| 4 | 1802-d11-r1 | 669 (100) | 759 (60) | 692 (100) | 723 (90) | 753 (80) |
| 5 | 1804-d11t-r1 | 586 (100) | 734 (90) | 713 (100) | 611 (100) | 738 (80) |
| 6 | 1806-d11p-r1 | 626 (100) | 618 (100) | 635 (90) | 690 (60) | 731 (90) |
| 7 | 1808-s0-r2 | 556 (100) | 549 (100) | 621 (100) | 708 (70) | 552 (100) |
| 8 | 1810-d11-r2 | 640 (100) | 769 (70) | 682 (80) | 727 (90) | 675 (90) |
| 9 | 1813-d11t-r2 | 550 (100) | 818 (50) | 767 (80) | 774 (60) | 730 (90) |
| 10 | 1815-d11p-r2 | 646 (100) | 698 (90) | 610 (100) | 730 (90) | 737 (90) |
| 11 | 1817-base-r2 | 539 (100) | 542 (100) | 538 (100) | 587 (100) | 562 (100) |
| 12 | 1819-d11-r3 | 794 (50) | 687 (90) | 697 (90) | 664 (90) | 780 (60) |
| 13 | 1821-d11t-r3 | 555 (100) | 547 (100) | 553 (100) | 554 (100) | 541 (100) |
| 14 | 1823-d11p-r3 | 538 (100) | 545 (100) | 579 (100) | 690 (100) | 694 (80) |
| 15 | 1825-base-r3 | 719 (80) | 771 (50) | 719 (80) | 702 (80) | 789 (70) |
| 16 | 1827-s0-r3 | 735 (70) | 798 (60) | 782 (70) | 659 (90) | 774 (80) |

### P util % mean per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (cold) | 82.2 | 78.3 | 71.8 | - | - |
| 2 | 1757-base-r1 | 69.2 | 67.3 | 77.7 | 77.4 | 81.4 |
| 3 | 1800-s0-r1 | 98.1 | 87.3 | 79.2 | 78.0 | 89.7 |
| 4 | 1802-d11-r1 | 88.9 | 82.0 | 86.6 | 83.0 | 80.8 |
| 5 | 1804-d11t-r1 | 90.3 | 77.9 | 78.3 | 89.9 | 76.7 |
| 6 | 1806-d11p-r1 | 85.1 | 84.8 | 86.0 | 80.6 | 76.7 |
| 7 | 1808-s0-r2 | 92.8 | 96.4 | 88.1 | 84.5 | 95.6 |
| 8 | 1810-d11-r2 | 87.1 | 76.8 | 83.9 | 77.2 | 79.6 |
| 9 | 1813-d11t-r2 | 90.5 | 71.3 | 73.3 | 72.7 | 74.1 |
| 10 | 1815-d11p-r2 | 81.3 | 75.6 | 79.4 | 73.8 | 73.7 |
| 11 | 1817-base-r2 | 100.3 | 100.2 | 97.9 | 100.7 | 93.3 |
| 12 | 1819-d11-r3 | 79.4 | 81.9 | 81.1 | 82.6 | 74.8 |
| 13 | 1821-d11t-r3 | 93.8 | 90.8 | 91.4 | 92.2 | 88.8 |
| 14 | 1823-d11p-r3 | 92.8 | 85.7 | 85.9 | 76.7 | 78.2 |
| 15 | 1825-base-r3 | 82.3 | 76.5 | 81.0 | 80.7 | 76.4 |
| 16 | 1827-s0-r3 | 80.0 | 74.7 | 75.3 | 84.3 | 75.0 |

### P MHz mean per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (cold) | 2107 | 2122 | 1926 | - | - |
| 2 | 1757-base-r1 | 1917 | 1927 | 1942 | 1942 | 1917 |
| 3 | 1800-s0-r1 | 1933 | 1927 | 1922 | 1917 | 1918 |
| 4 | 1802-d11-r1 | 1945 | 1944 | 1945 | 1944 | 1945 |
| 5 | 1804-d11t-r1 | 1942 | 1942 | 1940 | 1942 | 1941 |
| 6 | 1806-d11p-r1 | 1942 | 1942 | 1943 | 1939 | 1929 |
| 7 | 1808-s0-r2 | 1945 | 1945 | 1945 | 1945 | 1911 |
| 8 | 1810-d11-r2 | 1932 | 1930 | 1931 | 1930 | 1922 |
| 9 | 1813-d11t-r2 | 1940 | 1938 | 1939 | 1938 | 1938 |
| 10 | 1815-d11p-r2 | 1939 | 1938 | 1932 | 1937 | 1940 |
| 11 | 1817-base-r2 | 1922 | 1934 | 1934 | 1936 | 1929 |
| 12 | 1819-d11-r3 | 1927 | 1920 | 1914 | 1933 | 1928 |
| 13 | 1821-d11t-r3 | 1936 | 1935 | 1913 | 1916 | 1916 |
| 14 | 1823-d11p-r3 | 1941 | 1936 | 1942 | 1938 | 1942 |
| 15 | 1825-base-r3 | 1922 | 1920 | 1921 | 1921 | 1917 |
| 16 | 1827-s0-r3 | 1923 | 1918 | 1908 | 1936 | 1933 |

### E util % mean per bin

| seq | run | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s |
|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (cold) | 76.4 | 71.2 | 65.2 | - | - |
| 2 | 1757-base-r1 | 63.0 | 61.6 | 51.8 | 37.4 | 40.3 |
| 3 | 1800-s0-r1 | 35.5 | 40.5 | 43.9 | 44.5 | 39.5 |
| 4 | 1802-d11-r1 | 38.0 | 41.5 | 39.1 | 40.0 | 40.7 |
| 5 | 1804-d11t-r1 | 34.5 | 39.6 | 38.9 | 34.6 | 39.2 |
| 6 | 1806-d11p-r1 | 35.5 | 35.2 | 34.8 | 36.7 | 37.7 |
| 7 | 1808-s0-r2 | 33.0 | 33.6 | 34.7 | 37.1 | 32.5 |
| 8 | 1810-d11-r2 | 36.6 | 39.3 | 36.9 | 38.1 | 36.3 |
| 9 | 1813-d11t-r2 | 31.7 | 39.3 | 37.9 | 37.7 | 37.2 |
| 10 | 1815-d11p-r2 | 34.9 | 35.6 | 32.9 | 37.3 | 36.7 |
| 11 | 1817-base-r2 | 33.3 | 33.3 | 33.3 | 36.1 | 33.4 |
| 12 | 1819-d11-r3 | 39.9 | 37.7 | 37.8 | 36.7 | 39.6 |
| 13 | 1821-d11t-r3 | 32.3 | 32.2 | 32.5 | 32.4 | 32.7 |
| 14 | 1823-d11p-r3 | 32.8 | 31.9 | 33.8 | 36.4 | 35.9 |
| 15 | 1825-base-r3 | 38.3 | 39.5 | 38.5 | 37.6 | 40.6 |
| 16 | 1827-s0-r3 | 38.4 | 41.1 | 39.8 | 36.9 | 39.5 |

Slow bins (scored runs):

| run | bin | fps | x run median bin | E MHz | E<800 share % | P util % | P MHz | E util % | E mean < 800 | P util >= 90 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1800-s0-r1 | 0-10 s | 284.9 | 0.85 | 581 | 100 | 98.1 | 1933 | 35.5 | yes | yes |
| 1804-d11t-r1 | 0-10 s | 296.4 | 0.82 | 586 | 100 | 90.3 | 1942 | 34.5 | yes | yes |
| 1804-d11t-r1 | 30-40 s | 303.7 | 0.84 | 611 | 100 | 89.9 | 1942 | 34.6 | yes | no |
| 1813-d11t-r2 | 0-10 s | 287.2 | 0.77 | 550 | 100 | 90.5 | 1940 | 31.7 | yes | yes |

- bins of scored runs: 75; slow: 4 in 3 runs (1800-s0-r1, 1804-d11t-r1, 1813-d11t-r2)
- slow bins (n=4): E mean < 800 in 4; E<800 share >= 50% in 4; P util >= 90 in 3; both E<800 and P>=90 in 3; neither in 0
- other bins (n=71): E mean < 800 in 65; E<800 share >= 50% in 66; P util >= 90 in 13; both E<800 and P>=90 in 13; neither in 6
  - 1800-s0-r1: slow bins E 581 MHz / P util 98.1 vs other bins E 761 / P util 83.5
  - 1804-d11t-r1: slow bins E 599 MHz / P util 90.1 vs other bins E 728 / P util 77.6
  - 1813-d11t-r2: slow bins E 550 MHz / P util 90.5 vs other bins E 772 / P util 72.8
- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin E MHz mean: n=75 rho=0.43 (perm p 0.000)
- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin E<800 share: n=75 rho=-0.42 (perm p 0.000)
- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin P util mean: n=75 rho=-0.46 (perm p 0.000)
- my bin fps vs Agent 8's w5.json stat_bins: 78 bins compared, max |diff| 0.000 fps
- Agent 8's phase.json slow_bins_s: empty for all 16 runs (its criterion differs from the 0.85 x median rule here)
- window fps/frames from perf.csv vs frames.json: all 16 runs agree

## 5. Spearman rank correlations across scored runs (window fps = frames / summed frame time)

| run set | fps vs | n | rho | perm p (two-sided) |
|---|---|---|---|---|
| scored | (a) window E<800 share | 15 | -0.688 | 0.0058 |
| scored | (b) window mean e_eff_mhz | 15 | 0.846 | 0.0003 |
| scored | (c) window mean p_util_pct | 15 | -0.957 | 0.0001 |
| scored | (d) run order (seq) | 15 | 0.036 | 0.8977 |
| scored | extra: window mean p_eff_mhz | 15 | -0.071 | 0.8003 |
| scored | extra: window mean e_util_pct | 15 | 0.600 | 0.0197 |
| scored | extra: onset s (never = 999) | 15 | -0.193 | 0.4883 |

Scored runs by window fps (ascending):

| run | arm | seq | fps | win E<800 % | win E MHz | win P util % | win P MHz | run.json E MHz | run.json P util % | onset s |
|---|---|---|---|---|---|---|---|---|---|---|
| 1821-d11t-r3 | d11t | 13 | 277.1 | 100 | 551 | 91.4 | 1923 | 551.0 | 91.38 | 4 |
| 1817-base-r2 | base | 11 | 289.2 | 100 | 554 | 98.5 | 1931 | 554.0 | 98.5 | 4 |
| 1808-s0-r2 | s0 | 7 | 309.9 | 94 | 597 | 91.5 | 1938 | 597.0 | 91.49 | 21 |
| 1800-s0-r1 | s0 | 3 | 333.4 | 68 | 725 | 86.4 | 1923 | 725.0 | 86.44 | 40 |
| 1823-d11p-r3 | d11p | 14 | 335.3 | 96 | 609 | 83.8 | 1940 | 609.0 | 83.85 | 2 |
| 1804-d11t-r1 | d11t | 5 | 338.5 | 94 | 676 | 82.6 | 1941 | 676.0 | 82.61 | 13 |
| 1806-d11p-r1 | d11p | 6 | 343.3 | 88 | 659 | 82.4 | 1939 | 659.0 | 82.41 | 3 |
| 1802-d11-r1 | d11 | 4 | 350.3 | 86 | 719 | 84.3 | 1945 | 719.0 | 84.27 | 6 |
| 1810-d11-r2 | d11 | 8 | 351.3 | 86 | 699 | 80.9 | 1929 | 699.0 | 80.91 | 35 |
| 1819-d11-r3 | d11 | 12 | 352.5 | 76 | 725 | 80.0 | 1924 | 725.0 | 79.96 | 2 |
| 1825-base-r3 | base | 15 | 355.6 | 72 | 740 | 79.4 | 1920 | 740.0 | 79.36 | 22 |
| 1815-d11p-r2 | d11p | 10 | 356.9 | 94 | 684 | 76.8 | 1937 | 684.0 | 76.78 | 2 |
| 1813-d11t-r2 | d11t | 9 | 358.7 | 76 | 729 | 76.4 | 1938 | 729.0 | 76.37 | 1 |
| 1827-s0-r3 | s0 | 16 | 360.0 | 74 | 749 | 77.9 | 1924 | 749.0 | 77.88 | 2 |
| 1757-base-r1 | base | 2 | 384.6 | 26 | 1174 | 73.3 | 1931 | 1174.0 | 73.32 | 87 |

## 6. Agent 1's claim (SESSION2 18:34)

Claim: the 3 slowest runs (base-r2 1817, d11t-r3 1821, s0-r2 1808) are the ones with P util 91-98.5 %% and the lowest E clocks (551-597 MHz); the fastest, base-r1 1757, had E at ~1174 MHz.

- 3 slowest by window fps: 1821-d11t-r3 277.1 fps, 1817-base-r2 289.2 fps, 1808-s0-r2 309.9 fps -> same as the claimed set {1817, 1821, 1808}
- fastest: 1757-base-r1 384.6 fps (claimed 1757-base-r1)
- P util %, 3 slowest: mine 1821 91.4, 1817 98.5, 1808 91.5; run.json sys.window 1821 91.38, 1817 98.5, 1808 91.49
  - other 12 scored runs: max P util mine 86.4 (1800-s0-r1), run.json 86.44 (1800-s0-r1)
- E MHz, 3 slowest: mine 1821 550.9, 1817 553.8, 1808 597.0; run.json sys.window 1821 551.0, 1817 554.0, 1808 597.0
  - other 12 scored runs: min E MHz mine 609 (1823-d11p-r3), run.json 609.0 (1823-d11p-r3)
- fastest 1757-base-r1: E MHz mine 1174, run.json 1174.0; P util mine 73.3, run.json 73.32
- top 4 by window P util (mine): 1817-base-r2 98.5, 1808-s0-r2 91.5, 1821-d11t-r3 91.4, 1800-s0-r1 86.4
- lowest 4 by window E MHz (mine): 1821-d11t-r3 551, 1817-base-r2 554, 1808-s0-r2 597, 1823-d11p-r3 609


## 7. Notes added after the script run (helper, 19:53)

- Log line types across runs (log_types.txt next to this file, made by log_types.py in this folder; Toypad payload bytes collapsed): besides the proof lines (1 ms line: d11/d11t/d11p 1 each, others 0; precise line: d11p 1 each, others 0), the only lines whose count differs between runs are the `Toypad[Read ]` / `Toypad[Write]` exchanges (Read = Write in every run: cold 10; base 10/10/12; s0 10/10/10; d11 10/10/10; d11t 12/12/8; d11p 10/10/10). That explains the 95-103 line counts. The other 43 line types have the same count in all 16 runs.
- Both proof lines are `[info] [core]`: `Host timer resolution set to 1 ms (background opt-out on)` and `TimerQueue: precise wait (timer_queue_precise_wait)`. The d11t runs log no line about REX_TIMER_WAIT_BLOCKING or a TimerQueue mode, so blocking is visible only in run.json env_set / params.env (and in rules.md R7's TimerQueue thread CPU of 4.0-4.5 %).
- Slow-bin rule limits: the 0.85 x own-median rule only flags changes inside a run. The two slowest runs, 1821-d11t-r3 and 1817-base-r2, are slow in all 5 bins (bin fps 258-320, E 538-587 MHz, P util 89-101 %) and have no flagged bin.
  - Borderline flag: 1800-s0-r1 0-10 s (ratio 0.848).
  - Near misses: 1808-s0-r2 40-50 s (261.7 fps = 0.853 x median; E 552 MHz, E<800 100 %, P util 95.6 %) and 1823-d11p-r3 0-10 s (0.870; E 538, P util 92.8).
- Stretches: the slow state flickers more than in W4b. 3+ stretches per scored run have a median of 7 (range 1-11; W4b median 1.5, range 1-6), and window E means sit at 551-749 MHz (1757: 1174) rather than at the ~550 MHz floor.
