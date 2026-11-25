# Overseer ruling (e): #19 allow-new patterns in logdiff-normalised form (2026-11-25 09:21)

- **Trigger:** r19b (build/agent3/runs/20261125-091819-r19b-async-nosplit) gave s4b_check LOOK.
  - NEW 1: `[warning] [gpu] d#d#_async_submit: needs d#d#_submit_split_kb above #, staying off`. This is exactly the planned WARN for row b.
  - r19_gate --row b --bin B19: PASS (exactly 1 async line at warning, split 0, init 0, watchdog 0).
- **Cause:** s4b_check (L785-797) matches --allow-new against logdiff's normalised lines, where digits become `#`. The LAUNCH-R19 pattern `d3d12_async_submit: needs` can never match. M3 re-ran it with `d#d#_async_submit: needs`: NEW 0 (+1 allowed), HINT PASS?, exit 0 (build/agent3/s4b/r19/checks-norm).
- **Ruling:** every LAUNCH-R19 --allow-new pattern is applied in normalised form:
  - `d#d#_async_submit: needs` (b),
  - `d#d#_async_submit: ` (c, g, j, d, f),
  - `d#d#_(async_submit|submit_split)` (e).
  This is a mechanical translation that allows nothing beyond what LAUNCH-R19 intends. Each row's reading quotes the allowed NEW line(s) verbatim, and r19_gate still checks their exact count and level.
- r19b's unexpected GONE (XamUserReadProfileSettings) is not judged: a 90 s title route vs the menu-route base.
- **r19b:** PASS?. r19-ok-b may be written citing this file.
