# N6 read-out fix (M12, S3T-12 item 3), staged

From M5's `build/agent5/session3/N6-NOTE-M12.md`: day windows log to `bench\agent5\day\status\`, but `run_gates.py`
(L16, L85) defaults to the night folder `bench\agent5\launch\status\`. No launcher change.

## What is staged

- `build/agent12/w6-gates-n6/`: a copy of `build/agent12/w6-gates/` (code, fixtures, docs; not the out-/gates-/err-
  evidence) with a patched `run_gates.py` (BD51120207017D27; original 61C29AA543373DC9 = w6-gates/HASHES.txt).
  It sits at the same depth as `w6-gates/`, so its REPO path and imports work unchanged.
- `build/agent12/session3/n6/n6-run_gates.diff` (367E97DBDE6647F1), headers `w6-gates/run_gates.py`.
- `build/agent12/session3/make_n6.py` (makes both; exact-anchor replaces), `n6/test-n6.ps1` (the tests).

The change (both options of the note):
1. `--status DIR` and `--window-log FILE` work as before (option 1: give `--status bench\agent5\day\status`).
2. Without `--status`, the kit searches both `bench/agent5/launch/status` and `bench/agent5/day/status` (those that
   exist) with the existing `find_window_log` per folder. An END-line or runner-file match beats a START-time match; a
   match in both folders at the same strength is "ambiguous" → no window log (G3/G12 say CHECK) and the user gives
   `--status`/`--window-log`. The report's "launcher window log" line names the folder ("found in ...").
3. Docstring and `--status` help updated. Three new selftests (runner match beats START match across folders;
   ambiguous; no match anywhere).

## Tests (01:32-01:33, Below Normal, outputs only in `session3/n6/`)

| check | baseline `w6-gates` | patched `w6-gates-n6` |
|---|---|---|
| `--selftest` | PASS 51/51 | PASS 54/54 (51 + 3 new) |
| W5 fixture `--expect` | EXPECT OK 57/57, exit 0 | EXPECT OK 57/57, exit 0 |
| W4b fixture `--expect` | EXPECT OK 53/53, exit 0 (gates exit 1 from G10, as recorded) | same |
| real night dirs (import test) | | W6 0009 → window-W6-0006.log, W4c 0239 → window-W4c-0236.log, W5b 0451 → window-W5b-0445.log, each "its END line names this out dir; found in bench\agent5\launch\status" |

## Not done (needs the Overseer's OK)

- Installing: copy `w6-gates-n6/run_gates.py` over `w6-gates/run_gates.py` and refresh `w6-gates/HASHES.txt`
  (run_gates.py line only). w6-gates is M12's own folder, but HASHES.txt is the recorded state, so I left it.
- Doc lines (M5's table): `W6-GATES.md` L86 and `build/agent12/HANDOFF.md` L181 should say "night:
  `bench\agent5\launch\status\`, day: `bench\agent5\day\status\`". `NIGHT-RESULTS.md` L13 is correct as it is (night
  windows). `w6_env_record.py` L19 is a docstring only; it takes `--gate-log FILE`.
- Only matters once RUN-DAY is installed and a day window has run (`bench/agent5/day/` doesn't exist now).
