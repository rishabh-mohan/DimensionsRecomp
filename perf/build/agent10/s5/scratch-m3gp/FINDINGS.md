# E10.2 static safety review: M3 gameplay kit (build\agent3\gameplay)

Read-only, done during the FREEZE (no scripts of the kit were run). Reviewed 2026-11-25 18:19-18:30.

## Hashes (sha256/16, 18:19): all match M10's list
| file | sha256/16 |
|---|---|
| RUN-EXPLORE.cmd | 338FD44F3531AB54 |
| RUN-GAMEPLAY.cmd | 5D06F70231F805F8 |
| gameplay-run.ps1 | 96D7FE95713FF3A3 |
| gameplay-watch.ps1 | B217825D7FA2F39E |
| gameplay_post.py | B12A7E11CBB1A9B2 |
| gen_gameplay_route.py | 6353647F0906AD2E |
| STEP1-FEASIBILITY.md | A59630BF4099623A |

Also read: harness\run-game.ps1 C2533FDFE9A3A494, harness\guard.ps1 7A71E72057A0C87F, harness\winhelper.cs 37619E3DA38CE249,
harness\legodimensions.toml B763DABBE2C5FE7A, harness\vpad\vpadhost.cs 5D9290416F057B07, harness\vpad\xinput1_4.c 948E0A39BE45FD08,
build\agent3\toypad\toypad_sidecar.py, toypad_client.py, ldtag.py (write sites only), build\agent3\s4b\holdwatch.ps1,
build\agent2\session3\verify-bins.py (write sites only).

## 1. Kill sites
| site | call | target PID source | verdict |
|---|---|---|---|
| gameplay-run.ps1 L209 | Stop-Process -Id -Force | `$sp/$hp/$wp` from Start-Process -PassThru (L194-199); handles held (L200) so the PID cannot be reused; only if still alive after 240/30/60 s | OK, own PIDs |
| run-game.ps1 L302 | LdHarness.CloseAll($gamePid) = WM_CLOSE to visible windows of that PID (winhelper.cs L171-176, Windows() filters by PID L68-79) | `$p = Process.Start($psi)` (L233-234) | OK, own PID |
| run-game.ps1 L302 | $p.CloseMainWindow() | same `$p` | OK |
| run-game.ps1 L304 | $p.Kill() after CloseTimeoutSec (60 s) | same `$p` | OK |
| holdwatch.ps1 L38 | Stop-Process -Id $p.Id -Force, only when perf-notes\WINDOW-HOLD.txt exists | Get-Process legodimensions filtered by `Path -like "<RunsRoot>\*"` and `StartTime >= NotBefore-2` (L25-26); RunsRoot = build\agent3\gameplay\runs | OK (name + path + start time filtered; see N1) |
| gameplay-watch.ps1 | none ("touches no process"); Get-Process only to find the game by path under the run dir (L92) | - | OK |
| toypad_sidecar.py / toypad_client.py / gameplay_post.py / gen_gameplay_route.py | none | - | OK |
| run-game.ps1 L84-88, gameplay-run.ps1 L102-103 | Get-Process by name: refusal only, no kill | - | OK |

No kill by name or by window title. No taskkill.

## 2. Sidecar / helper lifetime
- Normal end: the sidecar ends on <run>\summary.json (toypad_sidecar.py L293-306) or at --timeout = Seconds+240 = 1140 s (L252, L308; args gameplay-run L138); --find-timeout 150 s if no run dir (L208-211). holdwatch ends when the game exits (L32-44) or after 150 s if no game is found (L24-29). The watcher ends 5 s after the game is gone or at Seconds+240 (gameplay-watch L83, L93-94). gameplay-run waits 240/30/60 s, then Stop-Process by own PID (L208-211).
- Game crash: run-game sees HasExited (L246), writes run.json, runstats writes summary.json, so the sidecar ends. holdwatch ends via WaitForExit. The watcher ends after 5 s.
- Script exception in gameplay-run: there is no try/finally around the arm loop (L185-215). Helpers are not stopped, but all are self-bounded (at most about 19 min). Nothing outlives that.
- Ctrl-C or console close: holdwatch and the sidecar share the console (-NoNewWindow, L194/L196), so they die along with gameplay-run and run-game. The game is a GUI process started by run-game (UseShellExecute=false, L183) and does not get the Ctrl-C. run-game has no try/finally after Process.Start (L233-306). Result: the game is ORPHANED (no WM_CLOSE, no kill, and no WINDOW-HOLD protection because holdwatch is dead). The vpad state file can also keep the last held stick or buttons. Only the hidden watcher (L198, own console) survives, bounded at 1140 s, and it only screenshots. -> SHOULD S2.
- Network: toypad_client.connect uses only ("127.0.0.1", port) (toypad_client L54). The port is --port, else env REXGLUE_TOYPAD_PORT/XENIA_TOYPAD_PORT, else 9191 (L38-43). The sidecar replaces it with the port from OUR run's game.log line "Toypad listener active on 127.0.0.1:<port>" (sidecar L32, L257-260). It only sends LOAD/REMOVE after that line and the trigger (L271, L287-292). Tags are memory-only (path length 0, client L158). Nothing beyond 127.0.0.1.

## 3. User data
- run-game: user_data_root = <run>\user (L117-119), written into the run-dir toml (L148, L155-156). harness\legodimensions.toml is only read (L142). Its game_data_root/update_data_root point to WS game\disc and game\tu23 (toml L20-21), which the game reads. Its user_data_root (game\user, L22) is overridden.
- Args: --native_settings_load=false, --discord_rpc=false, log/perf in the run dir (run-game L180-181). Inherited LEGO_*/PLUME_* env vars are removed (L185), e.g. no LEGO_NATIVE_PSO_AUX_UNLOCKED leaks in. LEGO_NATIVE_TRACE_DIR goes to build\agent3\gameplay\trace-native-<stamp> (gameplay-run L132, L187).
- No APPDATA/USERPROFILE/Documents/Saved Games/registry writes in any reviewed script. %LOCALAPPDATA%\CrashDumps is only listed (run-game L328-329).
- Evidence from M16's native4bp smoke run (same harness): new items only in the run dir (cache\, user\B13EBABEBABEBABE\5752084B\..., csv/log/json). The hard-linked binaries were not modified.
- Not verifiable statically: game-side writes outside user_data_root (e.g. GPU driver caches). These are not user profile data.

## 4. Pinned bins
- Pinned dirs (build\agent16\pack\native4bp-bin, build\agent2\devfinal2-bin) are only read: MANIFEST hash (gameplay-run L90-92), verify-bins.py (writes only with --out, which is not passed; verify-bins L63), Get-FileHash and Copy-Item SOURCE (L57-64).
- Copy targets: build\agent3\gameplay\bin-native / bin-xenos only (L72-75, L63). Each copy is re-hashed and verify-bins is run on it (L64, L123).
- run-game runs from the COPY (-BinDir $arm.copy, L130). The run-dir mirror hard-links to the copy, not to the pinned dir (run-game L104-111). The vpad DLL is copied into the run dir only (L174). run-game refuses if BinDir has its own xinput1_4.dll (L168).
- The runs root is build\agent3\gameplay\runs (L44), never inside a bin dir. CWD = run dir (run-game L183). Shots go to gameplay\shots\<stamp> (L46), plus logs\, post\, LATEST.txt, trace-*. All are inside the kit.
- Remove-Item: only gameplay\dryrun-runs, recursive, after a reparse-point check (L174-176). It deletes hard links, not their targets. run-game removes only its own profile.trigger (L254, L294).
- A pinned file is never a write target. Even if bin-<arm> files were hard links to pinned files, the hash would be equal, so no Copy-Item would happen (L63).

## 5. Input and screenshots
- The vpad is a shared-memory state file <run>\vpad-state.bin (vpadhost.cs L231-234), read by the xinput1_4.dll copy in the run dir, which only our game loads (AGENT3_VPAD env, run-game L188). vpadhost has no SendInput/PostMessage/keybd/SetForeground. XInputGetKeystroke hands VK_PAD events to the game in-process only (xinput1_4.c L196-221). No global keystrokes.
- winhelper.Press (SendInput) exists but is not called by run-game, the kit or vpadhost.
- Screenshots: gameplay-watch finds our game by process path under the run dir (L92) and captures `MainWindowHandle`'s CLIENT rect via CopyFromScreen (L36-40, L48-53, L100-105). CopyFromScreen copies SCREEN PIXELS of that rectangle. If another window covers the game (game not foreground), that window's content is saved. The foreground flag is only recorded (L101, L106), and the capture is not skipped. -> SHOULD S1. Compare winhelper.Shot L148, which screen-copies only when foreground.

## 6. Guards
| guard | where | status |
|---|---|---|
| foreign/any game running | gameplay-run L102-103; run-game L84-88 (no -AllowConcurrent passed) | refuse |
| WINDOW-HOLD.txt | gameplay-run L95-96 (start), L186 (between arms), holdwatch during the arm | refuse/abort |
| WINDOW-GO | not checked (no perf-notes\WINDOW-GO.txt exists right now) | missing (S3) |
| Agent 8 runners | harness\guard.ps1 L14 regex run-matrix.ps1, run-timing.ps1, first-boot.ps1, RUN-TIMING-MATRIX.cmd; gameplay-run L104-106 and run-game L90-94 | live check 18:22: detects `pid 9196 run-matrix.ps1` (S5 window), so a run now WOULD REFUSE. window-s5.ps1 / RUN-WINDOW-S5.cmd are not in the regex, so gaps before/after run-matrix are not covered (S3) |
| day launcher | gameplay-run L97-101 (waiting-for-quiet / running) | state now `waiting-for-go`: not refused |
| hidden desktop | gameplay-run L107-110 unless allowhidden | refuse |
| RAM < 6 GB | L111-113 | refuse |
| compile running | none | missing (NIT) |
| second gameplay-run instance | none (no lock) | race possible (N1) |

## Findings
BLOCKER: none.

SHOULD
- S1 gameplay-watch.ps1 L100-106: captures the screen rect even when the game is not foreground, so it can save overlapping user windows (privacy). Fix: skip (or note "not foreground, no shot") when `$fg` is false, as winhelper.cs L148 does.
- S2 gameplay-run.ps1 L185-215 + run-game.ps1 L233-306: no try/finally. Ctrl-C or console close leaves the game orphaned with no hold protection (holdwatch and sidecar share the console, L194/L196). Fix: a finally block that closes the game found by path under the run dir and start time (as holdwatch L25-26). Or at least document "do not Ctrl-C; if you did, close the game whose path is under build\agent3\gameplay\runs".
- S3 Guards (gameplay-run L95-106; guard.ps1 L14): no WINDOW-GO / window-s5.ps1 / RUN-WINDOW-S5.cmd check. The S5 window is caught only while run-matrix.ps1 runs. Fix: add these to the kit's refuse list (guard.ps1 is harness-owned), and start only on explicit clearance after the S5 window.
- S4 dryrun is not light I/O: Sync-Copy hashes and copies both pinned bins (L55-69, L119-126; it runs even with refusals, L114-117), verify-bins x4, and selftests. Do NOT run it, even dryrun, during the FREEZE.

NIT
- N1 No kit lock: two instances can both pass L102 and Sync-Copy into the same bin-<arm> at once. holdwatch would also match the other instance's game (same runs root). Fix: a lock file.
- N2 holdwatch FindTimeoutSec 150 (holdwatch L11, L29): if the game isn't found in time, holdwatch exits 1 and the arm runs without hold protection. gameplay-run only checks holdwatch afterwards (L208-212).
- N3 Sync-Copy L63 Copy-Item -Force onto bin-<arm> files that earlier run dirs hard-link, so it rewrites those older runs' files (harmless). L66 checks extra files only, not extra subdirectories in the copy.
- N4 starter_tags writes tags into build\agent3\toypad\tags if missing (toypad_client L140-142, ldtag L172-183). That is outside the kit (M3's own dir), so "Writes only build\agent3\gameplay\" (RUN-*.cmd L6-7) is slightly inaccurate.
- N5 `python` resolves to the WindowsApps app-execution alias. CreateProcess launches the target directly, so `$sp.Id` should be python itself (not verified at runtime). The sidecar is self-bounded anyway.
- N6 harness\legodimensions.toml L20-23 hard-codes absolute profile paths (harness hygiene, not the kit).

## Proposed verdict: SAFE-IF
1. Started only after the S5 window ends, on explicit clearance. Not even dryrun during the FREEZE (S3, S4).
2. The operator does not Ctrl-C or close the console mid-arm, or closes the orphaned game (path under build\agent3\gameplay\runs) by hand (S2).
3. The game window stays unobstructed during the run, or S1 is fixed first.
Kill, user-data, pinned-bin and input handling are clean.
