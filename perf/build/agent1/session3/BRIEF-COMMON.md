# Session 3 common brief (all managers M2-M12)

Started 2026-11-25 01:15 by the Overseer (grid Agent 4, acting as the old orchestrator "Agent 1").
Workspace root (WS) = `<workspace>`. All paths below are relative to WS.

## Who you are

The sprint was paused on Nov 23 with 12 peer agents. agy-grid changed: old Agents 2-12 are now
Managers (subagents of the Overseer). Manager **MN is the successor of old Agent N**: you own what
old Agent N owned, and your working folder is `build/agentN/`. You may start agy-grid-employee
subagents for big independent pieces; give each a self-contained brief and verify its result.

Read first: `perf-notes/RESUME.md` (sections 1, 6 and 7 at least), `build/agent1/HANDOFF.md`,
then your own `build/agentN/HANDOFF.md`. RESUME is the source of truth where they differ.

## Hard rules

1. **Never close, kill or disturb Minecraft** (`Minecraft.exe`, `Minecraft.Windows.exe`) or any
   process you didn't start. The user is playing right now. Before running ANY old script that kills
   or "cleans up" leftover processes, read it and confirm it only targets the game exe it launched
   (rexlego / legodimensions bins). If unsure, don't run it; ask the Overseer.
2. **No timed windows** and no night/day launcher starts: the user is at the PC, so timing doesn't
   count (RESUME section 7 step 0). Never write GO files.
3. **Machine-load policy (updated 01:36, the user left the PC for the night; Minecraft is closed):**
   one game at a time, never during a build or a timed window. Builds only by M2 (max 2 threads,
   Idle) and only when the Overseer says. Game runs only by the manager the Overseer gives "RUN GO".
   Timed windows only through the Overseer's night launcher. Quiet-host rows: no build running.
   Paper work (reading, writing diffs/plans/checkers, ratings, hashing files, dry runs, python/ps
   scripts that don't launch the game or a compiler) is fine now. Run such scripts at Idle/BelowNormal
   priority.
4. **Git:** only the Overseer commits or pushes. Never commit, push, stash, reset or checkout in
   `DimensionsRecomp/` or `DimensionsRecomp/rexglue-sdk/`. Don't edit tracked source in place; stage
   diffs/copies under your `build/agentN/`.
5. **Write only** under your own `build/agentN/` (and `bench/agentN/` if you owned it), unless the
   Overseer assigns you another file. Don't edit `perf-notes/` (M11 owns doc updates via the Overseer)
   or another agent's folder. Never copy `cache/` or seeds between bin dirs.
6. You can message only the Overseer. Anything another manager must do (a rating, a build, an
   install) goes to the Overseer as a request; it relays.
7. Numbering: "#N" is an S4 item; grid tasks are "task #N" (RESUME L7). Session-3 tasks are "S3T-n".

## Reporting

Send the Overseer short messages: (a) when you hit a dependency/decision you need, (b) when your
current work is done. End with: what changed (files + sha256 prefix of key outputs), how you
verified it, open issues, what you're blocked on. Keep a log at `build/agentN/SESSION3.md`.
