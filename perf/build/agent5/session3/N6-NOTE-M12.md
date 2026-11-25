# N6 note for M12 (read-out side; from M5, S3T-5, 2026-11-25)

N6 (Agent 10, `build/agent10/t27/day-draft-rating.md` L43; RESUME §6 item 6): Agent 12's read-out has to look in
`bench\agent5\day\status\` for day windows.

**No launcher change.** By design every launcher writes its status next to itself (`<own folder>\status\`), and the
day launcher is a separate install in `bench\agent5\day\` so that `bench\agent5\launch\` stays frozen. README-DAY.md
L87 (9739BCF8) already says where day windows log. So N6 is fixed on the read-out side only; the draft is unchanged.

**Where the read-out kit assumes the night folder** (found by grep, not edited; M12 owns these files):

| file | line | what |
|---|---|---|
| `build/agent12/w6-gates/run_gates.py` | L16, L85 | `STATUS_DIR` defaults to `bench/agent5/launch/status`; `--status DIR` / `--window-log FILE` already override it |
| `build/agent12/w6-gates/w6_env_record.py` | L19 | docstring names `bench/agent5/launch/status/`; it takes `--gate-log FILE` |
| `build/agent12/w6-gates/W6-GATES.md` | L86 | example command with `--gate-log bench\agent5\launch\status\window-<id>-<HHmm>.log` |
| `build/agent12/w6-gates/NIGHT-RESULTS.md` | L13 | "Window logs are in `bench/agent5/launch/status/`" |
| `build/agent12/HANDOFF.md` | L181 | "grep the window log in `bench/agent5/launch/status/` for the kill lines" |

**Minimal fix (M12's choice):**

1. For a day window, call the kit with `--status bench\agent5\day\status` (or `--window-log` / `--gate-log` with the
   day folder's `window-<id>-<HHmm>.log`). Nothing else differs: same log format, same runner, same matrix out dirs
   (`build/agent8/matrix/<stamp>`), same GO/HOLD/STOP files in `perf-notes\`.
2. Optional, more robust: when `--status` is not given, search both `bench/agent5/launch/status` and
   `bench/agent5/day/status` for the window log that names the out dir (`find_window_log` L281-314 already matches
   by out dir, so a two-folder search can't pick the wrong window), and print which folder it used.
3. Update the docs lines above to say "night: `bench\agent5\launch\status\`, day: `bench\agent5\day\status\`".

How to tell a day window from a night one: mainly by the folder. The log's start line (run-day.ps1 L953) does not
name the script; the HOLD text says "Agent 5's day launcher (<path>)" (L545) instead of the night wording, and the
folder's `pins.txt` lists `run-day.ps1` and `RUN-DAY.cmd` instead of `run-night.ps1` and `RUN-NIGHT.cmd`.

Timing: this only matters once RUN-DAY is installed (condition 2) and a day session has run. Nothing is needed now.
