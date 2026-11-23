# Timing matrix: selftest matrix (fake exe)

- matrix: <workspace>\build\agent8\run-selftest\matrix-test\matrix-st.json (copy in matrix.json); out: <workspace>\build\agent8\run-selftest\matrix-recheck-214541
- started 2026-11-21 21:45, ended 21:47; 5 runs (2 OK), 4 scored; desktop WinSta0\exebox-KJISPVCVSTP6BBVATPFJSX2M7W; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: -Quick run; 5 of 5 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group g: ref A (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 0/2 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | ref |
| B | 2/2 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0.01 |  |  |  | ref has no OK runs |
| C | 0/0 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | SKIPPED: bin build\agent8\run-selftest\no-such-bin is missing or has no MANIFEST.txt (not staged yet?) |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | A | 0 | PROBLEM | False | 2.35 | 156 | 16 | 120 | 6 | 3 | 0.01 | wm_close 0.2 s | 2145-cold-A | crash artifacts: C:\Users\<user>\AppData\Local\CrashDumps\ppc_tests.exe.76160.dmp, <workspace>\build\agent8\run-selftest\matrix-recheck-214541\runs\2145-cold-A\ppc_tests.exe.76160.dmp / not timing: desktop WinSta0\exebox-KJISPVCVSTP6BBVATPFJSX2M7W is not WinSta0\Default, build processes: ninja:52928 |
| 2 | 1 | A | 1 | PROBLEM | False | 2.06 | 156 | 16 | 120 | 6 | 3 | 0.005 | wm_close 0.1 s | 2146-A-r1 | crash artifacts: C:\Users\<user>\AppData\Local\CrashDumps\ppc_tests.exe.90024.dmp, <workspace>\build\agent8\run-selftest\matrix-recheck-214541\runs\2146-A-r1\ppc_tests.exe.90024.dmp / not timing: desktop WinSta0\exebox-KJISPVCVSTP6BBVATPFJSX2M7W is not WinSta0\Default, build processes: ninja:52928 |
| 3 | 1 | B | 1 | OK | False | 2.07 | 156 | 16 | 120 | 6 | 3 | 0.011 | wm_close 0.2 s | 2146-B-r1 | not timing: desktop WinSta0\exebox-KJISPVCVSTP6BBVATPFJSX2M7W is not WinSta0\Default, build processes: ninja:52928 |
| 4 | 2 | B | 2 | OK | False | 2.02 | 156 | 16 | 120 | 6 | 3 | 0.016 | wm_close 0.2 s | 2146-B-r2 | not timing: desktop WinSta0\exebox-KJISPVCVSTP6BBVATPFJSX2M7W is not WinSta0\Default, build processes: ninja:52928 |
| 5 | 2 | A | 2 | PROBLEM | False | 2.02 | 156 | 16 | 120 | 6 | 3 | 0.005 | wm_close 0.1 s | 2147-A-r2 | crash artifacts: C:\Users\<user>\AppData\Local\CrashDumps\test_upload_buffer_pool_pre.exe.29340.dmp, <workspace>\build\agent8\run-selftest\matrix-recheck-214541\runs\2147-A-r2\test_upload_buffer_pool_pre.exe.29340.dmp / not timing: desktop WinSta0\exebox-KJISPVCVSTP6BBVATPFJSX2M7W is not WinSta0\Default, build processes: ninja:52928 |

## Skipped arms

- C: bin build\agent8\run-selftest\no-such-bin is missing or has no MANIFEST.txt (not staged yet?)
