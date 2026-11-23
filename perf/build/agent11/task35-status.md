# Agent 11 - task #35 status (saved 17:08 for the agy-grid restart)

No edit was in progress at the restart notice. No command has run under task #35: file tools only, since Agent 1's 'go' hasn't come.

## Done
- `bench/agent11/timerq_slowstate_3mode.ps1` (new, ASCII, PS 5.1): the 3-mode copy for W5's read-out (precise > blocking > spin; flags; per-arm MIXED). The original `bench/agent11/timerq_slowstate.ps1` is untouched (frozen W4b input). Not run yet; hash not taken yet.
- Path sent to Agent 8 (@@to 8, ~17:03), marked untested until 'go'.

## Prepared, not run
- `build/agent11/s4draft/run11.py` (`--dry` | `--apply`). It gates on draft 14C2A482 / 476 lines and SESSION2 L2600-2635, plus the W5 file hashes (5467F1BE, 4D7D689B). It makes 20 one-match subs: a "Changed since 15:54" list (W4b result, the order from W5 on, native re-pin once on native4b), Still open, §2b step 5, §2c (start rule, before-fps, W5/W6 rows, order paragraph), §4b, §5 and §6. Then pipe/LF/BOM checks, a scan of leftover S4c/re-pin/launcher lines, and a hashed backup before writing.
- S4-DRAFT.md is still 14C2A482 (476 lines), with no backup of it yet; run11 --apply takes one.

## Next, after resume + 'go' (check perf-notes/WINDOW-HOLD.txt before every command)
1. `python build\agent11\s4draft\run11.py --dry`. Fix failures, review the scan output, and add subs for §2a's S4c paragraph and any rows that still say the re-pin is open.
2. One subagent (read/stage/check only) checks the 3-mode script against W4b (`build/agent8/matrix/20261122-1541`):
   - Run the original with `-Since 20261122-1541`, filtered to that matrix, and the copy with `-Matrix 20261122-1541`.
   - Per run, onset_s, slow_pct, span_s and fg must be identical, and env must equal blocking. d11t must come out blocking, all others spin, with no flags.
   - An independent Python recompute must agree.
   - Synthetic cases go in `build/agent11/s4a/slowstate3-test/20990101-0000/runs/`. Note that run.json's `--log_file` arg points at the real W4b log, so remove it for the no-log cases.
3. Set CHECK and WAIT in run11.py, then `--apply`. Record the full sha256 and line count, and confirm the result to Agent 8.
4. Review Agent 5's launcher (`bench/agent5/launch/`) only when Agent 5 asks. Write `build/agent11/launcher-review/REVIEW.md` and send it to Agents 5 and 1.
5. Report `@@done 35:` with the S4-DRAFT sha256, line count and changes, the script path with its W4b check, and the review verdict.
