# Agent 11 handoff (task #25, Nov 23, final at 08:40)

`perf-notes/RESUME.md` is the main restart doc. This note covers only my files, my open item and how I edit.

## My files

| file | sha256 | size | state |
|---|---|---|---|
| `perf-notes/RESUME.md` | 7616A164… | 51662 B, 381 LF | final at 08:09, with deltas at 08:18 (#19's rate request) and 08:39 (Agent 10's NIT F1: the 07:33:42 installer refusal was N-4, not a running launcher). Agent 10 reviewed 9DA0A4C3… and found it accurate, with no BLOCKER or SHOULD (`build/agent10/t27/resume-review.md` B3AE5716…, "Final version") |
| `perf-notes/FINDINGS-AND-CHANGES.md` | 6C9D5495… | 105403 B, 410 LF | pass C at 08:27 |
| `perf-notes/S4-DRAFT.md` | 407A17F7… | 218394 B, 567 LF | pass C at 08:27 |
| `build/agent11/resume/facts-perfopt.md` | 81AA5DE9… | 26424 B, 143 LF | the fact sheet behind RESUME §2: committed state, switches, pins. Its S4-DRAFT line cites date from 06:19 |

- All four files use LF only, with no CR and no BOM.
- RESUME uses workspace-relative paths only (public grep: 0 hits). FINDINGS keeps its `file:///` links for the user, which is its convention.
- **On resume:** re-hash these four files. If one differs, someone else edited it, so read its diff against my backup before editing.

## How I edit

- **Every edit runs through a gated script:**
  - The script checks the file's sha and LF count first.
  - Each op's old text must appear exactly once in its line.
  - It writes a hashed backup `<name>.<HHMM>-<old sha8>.md` and a dry-run diff, then applies with `--apply --t=HH:MM`.
  - Python runs at Below Normal, one script at a time, with `python -B`.
- **Latest scripts:**
  - `build/agent11/s4draft/passc.py` covers FINDINGS and S4-DRAFT. Copy it for the next pass and update both gates.
  - `build/agent11/resume/rfinal3.py` covers RESUME. The next copy is rfinal4.py, gated on 7616A164… and 381 LF.
  - `build/agent11/resume/mkdiff.py` makes the diffs.
  - The diffs and logs sit beside the scripts. Backups: `build/agent11/s4draft/FINDINGS-AND-CHANGES.0827-7D46CC91.md`, `build/agent11/s4draft/S4-DRAFT.0827-A8EA6697.md` and `build/agent11/resume/RESUME.0839-9DA0A4C3.md`.
- **Keep line cites valid:**
  - FINDINGS edits stay within lines, because RESUME cites FINDINGS L141, L142, L146 and L147.
  - S4-DRAFT edits stay within lines, and new lines go only at the end. RATE-REQUEST cites S4-DRAFT L236 and L416, and the fact sheet cites L248, L252, L385-390, L393 and L401-409.
  - RESUME edits stay within lines too, so it keeps 381 lines.

## My open item after the break

- **The day-draft rating, with Agent 10, once Agent 1 posts it as a board task.** It is not part of #25.
  - Start with `build/agent5/day-draft/README-DAY.md`, section "For the agents", and Agent 10's `build/agent10/t27/day-draft-rating.md`.
  - The draft was regenerated at 07:34 from the installed run-night.ps1 565D30D4… (run-day.ps1 B67EBD6C…, test-day.ps1 410FB2EC…; 27/27 at 07:47:14, README-DAY L130). The hashes in `build/agent11/morning-todo.md` (the 23:17 request) are therefore stale: re-hash first.
  - The two known items may still be open: NIT 14 (the day launcher doesn't see a screensaver-saved.txt left behind when a night launcher was closed with the X) and run-day.ps1's `\d` (non-ASCII digits give exit 3 instead of 2).

## Bench and older work

- `bench/agent11/timerq_slowstate.ps1` (38A3F6AC…) stays frozen.
- `bench/agent11/timerq_slowstate_3mode.ps1` (E9049B33…, task #10) is its 3-mode copy (spin / blocking / precise), used in Agent 8's W5 and W6 read-outs.
- My task #10 launcher review is in `build/agent11/launcher-review/`.

## Rules I worked under

- Check `perf-notes/WINDOW-HOLD.txt` before every command, and make no tool calls while it exists.
- Only Agent 1 commits or pushes.
- No builds or timed runs without a task.
- Subagents only read, stage and check.
