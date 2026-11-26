# Next-session package (M3): EXPLORE3 + manual Toy Pad step test with story-shader dump

**Status:** prepared 04:55. **No kit file is changed by this package**, so there is no install, tamper or dryrun beyond the one extra dryrun in B0.

**Live kit (S1, G2-G4 closed):**

| File | sha256 |
|---|---|
| gameplay-run.ps1 | 28F7785BDB47FBDFCA0397BD0139AF5D82BB1EF9D28FFD1298C98CBAD09271BA |
| gen_gameplay_route.py | 2C1977DE3652DF2496F57C9D4B10D0E73008871F8DF3B516D62DB52D59004D50 |
| explore-route.txt | CB271440130C47ED8CBE8FAE804BD82F4B82EBA3C8C48C77D920AA563F91831F |
| gameplay-route.txt | 705A3A504BF6B669ECD237243C6AC93227D57EE80243A0815502B6ED173B073D |
| RUN-MANUAL.cmd | DC22DF4FCF57BF899C522521E318E79A623CD67F396C88A4E54D98BA1E739D70 |
| RUN-EXPLORE.cmd | 5B4A31A98F52F74C5510D3D4DB19ABB6F695F787A0F52C245D93D9E6913681BC |
| RUN-GAMEPLAY.cmd | 09304AC0606A3EED2DE3C66718463CE3C7CD6C72E4D080E3A436D56467436CD6 |

**G4 dryrun logs** (verified by M3: header, route `same`, ALL PASS):

| Log | sha256 |
|---|---|
| `logs\gameplay-dryrun-20261126-044830.txt` | DAC1FDC92C68F7DF055824898A954B78AAD0B418E3B8B3D3F17194E37785CEB2 |
| `logs\gameplay-dryrun-20261126-044916.txt` | 4414F34B26EB96595EC2293D21B103E157704DABA34108C7DE9179B52161876A |
| `logs\gameplay-dryrun-20261126-045001.txt` | F78B3A9975C31FE1057C28C7C855CEFCEF0288E07A1236833E8880EDE4A02F35 |

## A. EXPLORE3 (real run, scripted, no human input)

### A1. GO line

`build\agent3\gameplay\RUN-EXPLORE.cmd` (5B4A31A9), **with no args**.

- RUN-EXPLORE.cmd L51 calls `gameplay-run.ps1 explore %*`.
- ps1 L117: `explore` with no arm word → `@('native')`, so **native only**. This is the approved scope (G1).
- `-Seconds 1500` and the route explore-route.txt CB271440 (246 steps, 66 marks), the same as dryrun 044916.
- Never add `xenosonly` (not approved, B1) or `dump` (refused: exit 2).

### A2. During the run

- Don't use the screen, the keyboard or ctl files. The route and the sidecar do everything.
- Optional, read-only:

  ```powershell
  Get-Content <run>\game.log -Wait -Tail 0 | Select-String 'Native frontend transition|Toypad listener|speed 15'
  ```

- **Expected sequence:**
  1. fe 7 (install prompt), then pads white and tags placed.
  2. Intro, then **fe 12 (title)**, then `sleep 12`, then START tries.
  3. **12 → 13** after the accepted try.
  4. B, A, then **fe 5 pending=0 (TITLE GATE CHECK)**.
  5. 17, 47, 49, 54, 55, then 55 pending=0 (story).
  6. The 3 prompts: sidecar `fire 1/4`, then LOAD on pads 2 / 3 / 1.
- **New and expected:** about 6 min after story-00, the intro cutscene ends (all pads amber `99 42 0E`). ~30 s later, pad 3 starts a slow speed-15 `FF 00 18` blink: the Toy Pad zone step (post A6CA97C5 §4).
  - The sidecar does not answer it, by design.
  - The route's O / P / L2 / walk inputs will land during the cutscene and the step, and the tail shots will show the white portal.
  - **That is expected and not a regression.** The zone moves to the next pad every 120 s.

### A3. Post / report (T4, T5, G5-style; M3 writes it)

1. **Title gate:**
   - the number of the try that was accepted (1-6): the first `press START` followed by `current=13` within 10 s;
   - its delay after fe 12 (t(13) - t(12));
   - the **gate check** `current=5 pending=0`: hit or **TIMEOUT**. **A TIMEOUT means FAIL: record it and stop; ignore the route tail** (T5).
2. Each later front-end wait (17 / 47 / 49 / 54 / 55 / 55-0): hit or TIMEOUT, with the time.
3. Prompts: s-batman / s-gandalf / s-wyldstyle, LOAD or TIMEOUT. For each: fire n/4, prompt-done, load-confirm, any failsafe.
4. The zone step: start time, pad and colour, and the 120 s handoffs. This is to confirm what was seen in 041246.
5. Whether `stop` / `mark end` was reached before 1500 s, and the exit and close path.
6. Known post bug, to ignore: summary "median draws per 10 s: 0" reads perf.csv, which is dead on native. Use frames.csv.

## B. Next manual session: Toy Pad step test + story-shader dump

### B0. Gates before the GO (all needed)

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | **D4(a) ruling.** EXPLORE2 was **inconclusive** (its G4 stopped), so D4(a) as written is not met. **Proposed substitute evidence:** manual session 041246 had prompts batman 2 / gandalf 3 / wyldstyle 1 accepted on **fire 1/4**, with prompt-done and load-confirm each about 2 s later and no failsafe (toypad-events 73E7AC5E; post A6CA97C5 §2). | M10 | **MET by substitution** (980A1325 v1; proviso: a prompt missing fire 1/4 or a failsafe in the dump session = not conclusive, next session without dump) |
| 2 | **D4(c) trade-off.** If the zone-step test fails in a dump session, it is **not conclusive** and must be re-run without dump. Combining saves a session if it works, and costs one if it doesn't. | M10 / Overseer | **recorded, accepted risk** (980A1325 v2) |
| 3 | **D5 / P1:** M16's exe scan of the native4bp exe for the string `LEGO_DUMP_MISSING_SHADERS`. Idle priority, no game running; give found yes/no plus the exe sha8. | M16 | open? |
| 4 | **D3 on the S1 ps1:** `RUN-MANUAL.cmd dump dryrun`. The dump code is unchanged, but the ps1 sha changed (D97C9228 → 28F7785B), and G4 ran only plain dryruns. Expect: ALL PASS, `-Seconds 1200`, `LEGO_DUMP_MISSING_SHADERS=<abs>\shader-dumps-native-<stamp>` in the run-game -Env line, the DIAGNOSTIC line, and no dump dir left. Light, native-only. | Overseer GO, M3 checks | open |
| 5 | The hold file, the 1200 s cap, ctl rules (a)-(i) and M1-M6 from `post\manual-toypad-debug-plan.md` 7198352D apply unchanged (D4e). | all | - |

### B1. GO line

`build\agent3\gameplay\RUN-MANUAL.cmd dump` (DC22DF4F).

- The cmd passes `manual dump`, which gives the native arm only, 1200 s, and the env `LEGO_NATIVE_TRACE_DIR=…;LEGO_DUMP_MISSING_SHADERS=<kit>\shader-dumps-native-<stamp>`.
- The session is **DIAGNOSTIC**: frames.csv, fps, worst frames and missing-draw counts are void (D4d), because the miss cache is OFF and pool-copy hashing is on.
- Forms that are refused with exit 2, nothing written: `RUN-MANUAL.cmd dump xenosonly`, `RUN-EXPLORE.cmd dump`, `RUN-GAMEPLAY.cmd dump` (tamper C6AAE0FD).

### B2. Dump targets: no list is supplied to the game

- The mechanism is **untargeted** (PLAN-story-dump F2E16382 §1):
  - every placement miss is written once, deduplicated by XXH3, to `placement-containers\{vs,ps}-<16hex>.bin`, with one `missing_placement_shader_identity` event per container (shaders.cpp:146-207);
  - create-path misses go to the root dir (shaders.cpp:738). They are flagged, not packed (D6).
- **Cap: 256 containers per process.** The menus use slots first. The story and portal scenes come at about +6 and +12 min.
- **The target list is a post-check, not an input.** M16's `dump_post.py` (read-only on M3's dirs; writes only under build\agent16\dump) checks each target for a `placement-containers` file plus an identity event:
  - VS **0xAC44BC64**;
  - **the 34 story inserts and 46 draw-miss guests** from NOTE-story-misses-024219 B48DA281. **That note does not list all of them**, so M16 should send the exact list as a file before the session (via you);
  - the white-portal guests from NOTE-white-portal-0428 015E334B: VS 0xA7FA6E00, VS 0xA7FA8990, PS 0xA7FA6C00, PS 0xA7FA8750, PS 0xA8302100, and the known PS 0xAC53D0AC, PS 0xAC49B8F8;
  - the PLAN §5 targets 0xA81E1C30 and 0xA81E6820.
- If the identity count is ≥ 256, the post reports the capture as **capped and incomplete** (D6).
- For the portal guests to be captured, **the session must reach the portal/zone step** (about +12 min, §B4). It also helps to reach the pad-2 / pad-1 phases and, if the step clears, the next scene.

### B3. Key path, boot to story (you drive by hand with cc.ps1)

- Keys: J = A, K = B, Enter = START, D = right.
- Optional state watch, read-only:

  ```powershell
  Get-Content <run>\game.log -Wait -Tail 0 | Select-String 'Native frontend transition|Toypad listener|speed 15|99 42 0E'
  ```

This is the key sequence that worked in the 04:12 session (manual-keys.log 04:13:44-04:22:17), minus the test at 13.

- **cc.ps1 form.** Call it from a PowerShell session as `& $cc <keys>`, with `$cc = '<Overseer scratch>\cc.ps1'`.
  - **Don't use `powershell -File cc.ps1 -Keys a,b`**: -File passes `a,b` as one string.
  - Every call focuses the game, presses the keys, logs them to manual-keys.log and takes a screenshot. Use one call per step: look at the state, then press.

| Step | When (state / log) | cc.ps1 call | Expect |
|---|---|---|---|
| 1 | fe 7 `current=7` (install prompt), +2 s | `& $cc j` | pads white (`pad 3 mode 1 lit FF FF FF`); the sidecar loads the 3 tags 2 s later (listener LOAD pads 2 / 1 / 3) |
| 2 | after that | none: **hands off**; the intro runs by itself (04:13:44 → title 04:17:12, no keys) | fe 12 |
| 3 | fe 12 `current=12` (title "Press START") | wait **~18 s** after fe 12, then `& $cc Return` | 12 → 58 → 40 → **13** within ~3 s (04:12 session: +19 s, accepted at once). If there is no 13 within 10 s, `& $cc Return` again, every 10 s, **max 6**. A press at +3.8 s was ignored. |
| 4 | 13 | `& $cc j` (**not** Return: START at 13 does nothing) | → 0 (Updates panel) |
| 5 | 0 (Updates) | `& $cc j` | Store notice: `current=5 pending=0` |
| 6 | store notice | `& $cc j 'wait:3.4' k` | → **17** main menu (04:12 session: j, j, k ~4 s apart) |
| 7 | 17 | `& $cc j` if **New Game** is highlighted in the screenshot (it was in 04:12), else `& $cc 'd:0.25'` first | → 47 (save slots) |
| 8 | 47, +3 s | `& $cc j` (slot 1) | → 49 (confirm, default Yes) |
| 9 | 49, +3 s | `& $cc j` | → 52 / 53 / 54 (autosave notice) |
| 10 | 54, +3 s | `& $cc j` | → 55 (Toypad picture, "Select A") |
| 11 | 55, +3 s | `& $cc j` | → `current=55 pending=0`, then **story (state 0)** |

- From here, **no keys and no ctl** until §B4. The 3 prompts are the sidecar's job: in sidecar.out, `prompt <fig> fire 1/4`, then `prompt-done ok`, then the listener LOAD on pad 2 (batman), 3 (gandalf), 1 (wyldstyle), each within ~2 s, with the pulse stopping.

### B4. Expected timing (from 041246, offsets from launch; dump may slow it a little)

| Point | 041246 | Target this time |
|---|---|---|
| title fe 12 | +266 s | ~+270 s |
| story (state 0) | +571 s (it included a ~2 min test at 13) | **~+360 s** |
| batman, gandalf, wyldstyle prompts done | story +2 / +60 / +197 s | same |
| intro cutscene end (all pads amber) | story +328 s | ~+690 s |
| **zone step start T0** (pad 3 slow `FF 00 18` speed 15) | story +357 s (+928 s) | **~+720 s** |
| left for the step test | 272 s | **~480 s** |

### B5. ctl plan 001-006, final (zone step)

- Write `<run>\toypad-ctl\NNN.cmd` with one command line. It is taken once it is ≥ 0.5 s old and becomes `.done` (or `.err`) within ~1.5 s.
- **On `.err`: stop and report.**
- **T0** = the first `pad 3 mode 3 lit FF 00 18 (… speed 15)` after the all-pad amber.
- **Start at T0 + 25 s**, not earlier: the scene load ran 04:28:00-04:28:39, through T0 (04:28:14). The 120 s window leaves room.

| NNN | At | Command | Expected .done | Expected LED / screen | Then wait |
|---|---|---|---|---|---|
| 001 | T0+25 | `status` | `batman pad=2, gandalf pad=3, wyldstyle pad=1` | none | 3 s |
| 002 | T0+30, **and only after the scene load has ended** | `remove gandalf` | `REMOVE gandalf pad=3 … hangup-ok`, plus remove-confirm pad=3 | pad 3 slow `FF 00 18` (empty, so it wants wyldstyle). Possibly no change: it already showed this in 041246. | 5 s |
| 003 | T0+36 | `move wyldstyle 3` | `REMOVE wyldstyle pad=1; LOAD wyldstyle … pad=3`, plus confirms | **ACCEPT** = pad 3 stops blinking or changes, **and** another pad starts blinking (pad 2 predicted) or the scene moves on. Head icon changes from Wyldstyle. | 10 s |
| 004 | +5 s after pad 2 starts | `remove batman` | `REMOVE batman pad=2`, plus confirm | pad 2 slow `FF 6E 18` within 0.3 s (seen 04:31:00) | 5 s |
| 005 | +5 | `place gandalf 2` | `LOAD gandalf … pad=2`, plus confirm | **ACCEPT** on pad 2; pad 1 starts blinking, predicted slow `00 00 18` (empty, wants batman). Icon → Batman. | 10 s |
| 006 | +5 | `place batman 1` | `LOAD batman … pad=1`, plus confirm | **ACCEPT**: blinking stops, the portal or white scene resolves and the next scene or control returns | 15 s, then try a hand move (WASD / J) to confirm control |

**Rules (M10 rating C78F02DE, C1-C7):**
- **C1:** run 002-006 only if 001 shows **b2 g3 w1**. If the layout differs, **stop the ctl part and report**. Don't improvise a mapping.
- **C2:**
  - No ctl during a load or cutscene.
  - The start signal is the speed-15 slow blink after the all-pad amber.
  - Never send ctl within 10 s of a story prompt fire or before its prompt-done.
- **C3:** before each next file, check the `.done`, the listener confirm **and** the `Toypad: pad P …` LED line in game.log. Any `.err` → stop.
- **C4:** exactly **one retry** each at 003, 005 and 006, then stop and record.
  - 003 retry: `remove wyldstyle`, ≥3 s (C4 as amended in 980A1325), `place wyldstyle 3`.
  - 005 retry: `remove gandalf`, ≥5 s, `place gandalf 2`.
  - 006 retry: `remove batman`, ≥5 s, `place batman 1`.
  - No other commands until control returns.
- **C5:** send 005 **as soon as 004's remove-confirm is in**, so that b and g are both off for ≤15 s.
- **C7:** if the step hasn't started by about **+1050 s**, skip the ctl plan and keep the dump.
- 003 uses `move`, not `swap`: a swap would put gandalf back on a zone.
- **002 only after the scene load has ended** (C2; in 041246 the load ran to 04:28:39, after T0). `status` (001) is fine during the load.
- **Branch: the step has already moved to pad 2 when you start** (pad 3 solid, pad 2 blinking; M10 check 980A1325 B1). Skip 002/003 and run:
  - 004 `remove batman` → expect pad 2 slow `FF 6E 18`;
  - 005 `move gandalf 2` (not `place`: gandalf is still on pad 3, and `place` would `.err`) → expect ACCEPT on pad 2, then pad 1 blinking;
  - when pad 1 blinks: `remove wyldstyle`, then ≥3 s later `place batman 1` → expect ACCEPT, the step resolves.
  - One retry per step (C4: retry = `remove` the figure, ≥3 s, `place`/re-`move` it), then stop and record. Wyldstyle stays off the pads in this branch; that is expected.
- **Any other layout or state** (001 ≠ b2 g3 w1, step on pad 1 at start, unknown colours): stop the ctl part and report (C1). Keep the dump running.
- After 006, or after a stop: no more ctl in this session. Free-play tests (§5.4 of the post) need the step resolved, with ≥10 s between files.
- With dump on, a non-accept is **not conclusive** (D4c): re-test without dump. An accept on all 3 pads does count.
- Colour → figure, for the notes only: `FF 00 18` = wyldstyle, `FF 6E 18` = gandalf, `00 00 18` = batman. Fast red `FF 00 00` = a wrong figure is on the pad.

**Record for the post:**
- each NNN with its wall time;
- the LED line that followed, from toypad-events.csv;
- the head icon after each step;
- whether the white frame changed.
