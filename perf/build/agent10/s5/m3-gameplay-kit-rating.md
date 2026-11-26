# S5 rating: M3 gameplay kit (RUN-EXPLORE / RUN-GAMEPLAY)

M10, 2026-11-25 18:26. Static review only (FREEZE active; nothing run). The detailed read is by E10.2 (scratch-m3gp/FINDINGS.md). I re-checked the kill sites, the holdwatch filter, the helper reaping and the screenshot path myself.

Hashes are **PROVISIONAL**: M3 regenerates the routes after the freeze, so re-hash before the GO.

| File | sha256/16 | Bytes |
|---|---|---|
| build/agent3/gameplay/RUN-EXPLORE.cmd | 338FD44F3531AB54 | 939 |
| build/agent3/gameplay/RUN-GAMEPLAY.cmd | 5D06F70231F805F8 | 766 |
| build/agent3/gameplay/gameplay-run.ps1 | 96D7FE95713FF3A3 | 18001 |
| build/agent3/gameplay/gameplay-watch.ps1 | B217825D7FA2F39E | 7386 |
| build/agent3/gameplay/gameplay_post.py | B12A7E11CBB1A9B2 | 15811 |
| build/agent3/gameplay/gen_gameplay_route.py | 6353647F0906AD2E | 7011 |
| build/agent3/gameplay/STEP1-FEASIBILITY.md | A59630BF4099623A | 5560 |
| build/agent3/s4b/holdwatch.ps1 (used) | A4A591FCD8E8B8C6 | - |
| build/agent3/toypad/toypad_sidecar.py (used) | F7905A908D228527 | - |

Context, unchanged: harness/run-game.ps1 C2533FDF, guard.ps1 7A71E720, winhelper.cs 37619E3D, legodimensions.toml B763DABB, vpadhost.cs 5D929041.

## Verdict

**SAFE-IF G1-G5.** No BLOCKER.
- **Kills.** Every kill targets a PID the kit started, or our own game found by path under gameplay/runs.
- **User data and bins.** The user data root is `<run>/user`. The pinned bins are only read (copies go to gameplay/bin-*).
- **Network and input.** The sidecar talks only to 127.0.0.1 on the port our game logged. vpad input reaches only the game that loads the run-dir xinput1_4.dll.
- **Residual risks:**
  - screenshots of whatever covers the game window (S1);
  - a game orphaned on Ctrl-C or console close (S2);
  - a missing guard on window-s5 / RUN-WINDOW-S5 (S3).

## What I checked

- **Kill sites (verified).**
  - gameplay-run L208-209: Stop-Process -Id only on `$sp/$hp/$wp`. They come from Start-Process -PassThru (L194-199) and their handles are held (L200), so a PID cannot be reused. The stop fires only after 240/30/60 s of grace.
  - holdwatch L25-26 / L38: it stops only a legodimensions process whose Path is under gameplay/runs and whose StartTime is >= NotBefore-2 s, and only while WINDOW-HOLD exists. It cannot match M16's or Agent 8's games, which run from other roots.
  - run-game: WM_CLOSE by PID, then Kill of its own `$p` (L302-304).
  - No taskkill, and no kill by name or window title.
- **Helper lifetime.**
  - The sidecar ends on summary.json, at Seconds+240, or at its find timeout.
  - holdwatch ends when the game exits, or after 150 s if no game is found.
  - The watcher ends 5 s after the game is gone, or at Seconds+240.
  - gameplay-run then reaps any survivor by its own PID.
  - There is no try/finally: on a script exception the helpers stop themselves within about 19 min.
- **User data.** run-game writes the toml into the run dir with user_data_root=`<run>/user` and flags --native_settings_load=false and --discord_rpc=false, and strips inherited LEGO_/PLUME_ vars. There are no APPDATA, profile or registry writes. CrashDumps is only listed.
- **Pinned bins.** MANIFEST hash + verify-bins (no --out), then real copies into gameplay/bin-native and bin-xenos, re-hashed. The run-dir hard links point at the copies. The vpad DLL is copied into the run dir only. The only recursive delete is gameplay/dryrun-runs, after a reparse-point check (L174-176).
- **Screenshots (verified).** gameplay-watch L92 picks our game by process path under the run dir. L100-105 CopyFromScreen of its client rectangle. The foreground flag (L101) is only recorded.
- **Guards.** It refuses on any game running, WINDOW-HOLD (at start, between arms, and via holdwatch during each arm), a hidden desktop, less than 6 GB RAM free, a busy day launcher, and an Agent 8 runner (guard.ps1 regex). A live check by E10.2 at 18:22 saw run-matrix pid 9196, so a start now refuses.

## Conditions

- **G1.** Start only after the S5 window and the FREEZE, on the Overseer's GO. That includes dryrun, which copies and hashes both pinned bins (S4).
- **G2.** One unattended kit at a time: not alongside the M16 PSO kit (rated E54D1890, R1). Neither kit holds a lock, and the "game running" checks happen only at start or between arms.
- **G3.** Keep the game window unobstructed on the interactive desktop for the whole run, or fix S1 first. Otherwise a covering window's pixels (possibly user content) are saved as JPEGs.
- **G4.** No Ctrl-C or console close mid-arm. If it happens, close the orphaned legodimensions under gameplay/runs by hand (S2).
- **G5.** Re-hash all kit files after M3's route regeneration. If anything besides the routes and the generator output changed, send it back for a delta review.

## Findings

- **S1 (SHOULD).** gameplay-watch L100-106: skip the shot, or use PrintWindow, when the game is not foreground. winhelper.Shot already does this.
- **S2 (SHOULD).** run-game and gameplay-run have no finally, so Ctrl-C or a console close orphans the game. The game also loses its WINDOW-HOLD protection, since holdwatch dies with the console, and the vpad may stay held. Add a finally that closes the game found by path and start time. This harness issue applies equally to the M16 PSO kit.
- **S3 (SHOULD).** Add window-s5.ps1, RUN-WINDOW-S5.cmd and WINDOW-GO.txt to the refuse list. guard.ps1's regex covers only run-matrix, run-timing and first-boot, so the gaps before and after run-matrix inside a window are not covered.
- **S4 (SHOULD).** dryrun is not light: Sync-Copy of both pinned bins even when refusals exist, 4 verify-bins runs and the selftests. Refuse before copying, or document it as heavy.
- **N1.** No kit lock: two instances can race into Sync-Copy, and holdwatch would match the other instance's game.
- **N2.** holdwatch gives up after 150 s if it finds no game, so the arm runs without hold protection, and gameplay-run only notices afterwards.
- **N3.** Sync-Copy -Force rewrites files that older run dirs hard-link (harmless). Extra subdirs in the copies are not detected.
- **N4.** Missing toypad tags are written into build/agent3/toypad/tags, outside the kit, contrary to the "writes only gameplay/" claim in RUN-*.cmd L6-7.
- **N5.** `python` may resolve to the WindowsApps alias, so the PassThru PID may not be the real interpreter. The sidecar still stops itself.
