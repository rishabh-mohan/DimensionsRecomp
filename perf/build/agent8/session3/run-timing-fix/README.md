# run-timing.ps1 stop_line fix (draft, not installed)

**Problem:** `run.json` `sys_sampler.stop_line` is always null, and the run log line "sys.csv sampler: exit 0" and the summary.txt "sampler" line have no stop text. run-timing.ps1 L503 keeps only the sys.out.txt lines that match `'^sys-csv: stop'`, but sys-csv.ps1 prefixes every line with a clock and an offset (`07:35:23.053 +35.65s sys-csv: stop reason=game_exit ...`). This predates M8's runner install: the old sampler (LdSys b452d258, M3 run `build\agent3\runs\20261125-071741-s33-offsf`) prints the same prefix and its run.json is also null.

**Fix:** one line (L503). The pattern becomes `'(^|\s)sys-csv: stop '`. The trailing space keeps `stop_file=`/`stop_watch=` on the start/timing lines from matching. See `run-timing.diff`.

| | sha256 |
|---|---|
| bench\agent8\run\run-timing.ps1 (installed) | 75F4B5278BD75C1452CED72D5CE746708D048E5E4357B01BA3C69EF20D19D6D3 |
| run-timing.ps1 here | 9CCE982737C773D062EE38A459E07BD790094BB3B656BC5A3CF3A229552807B3 |

The file has no BOM and LF line endings; both are unchanged (byte-level replace). It parses with 0 errors.

**Offline test** of the new pattern (old pattern in brackets):
- the 4 smoke-run sys.out.txt files (new sampler): 1 match each [0]
- the M3 07:17 run (old sampler): 1 match [0]
- selftest bad-args outputs: 0 [0]

**Effect:** only text. `stop_line` is written to run.json and printed at L506 (run log) and L673 (summary.txt). No script reads `stop_line` (grep of bench\agent8\run\*.py, *.ps1 and bench\agent5\launch\*.ps1). Timing, flags and exclusion are unaffected.

**Install note:** run-night.ps1 and run-day.ps1 pin run-timing.ps1 at launcher start. Install it only when no launcher or runner is running. install-day.ps1 does not pin it.
