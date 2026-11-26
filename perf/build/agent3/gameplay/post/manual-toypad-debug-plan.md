# Manual Toypad debug session: test plan (M3)

GO target: `RUN-MANUAL.cmd` 2B60C24F, no args. No dump (D4a). The session ends itself at 1200 s.

## 0. Before the session
- Live `--on` specs (gameplay-run.ps1 L66-67), which the sidecar fires 1.0 s after a match. It re-fires every 15 s while the pad keeps pulsing, at most 4 fires.
  - pad 2: `00 00 16|00 00 05` -> batman
  - pad 3 (right): `F4 69 16|3D 1A 05` -> gandalf
  - pad 1 (centre): `F4 00 16|3D 00 05` -> wyldstyle
- Boot placement (ldtag.STARTER): batman pad 2, gandalf pad 1, wyldstyle pad 3.
  - The prompts therefore act as: batman = `replace batman`, pad 3 = `move gandalf 3`, pad 1 = `move wyldstyle 1`.
  - End state: batman 2, gandalf 3, wyldstyle 1.
- Files:
  - sidecar log: `build\agent3\gameplay\logs\<stamp>-native.sidecar.out.txt`
  - run dir: `build\agent3\gameplay\runs\<stamp>-gpman-native\`
  - ctl dir: `<run dir>\toypad-ctl\` (the sidecar.out line 7 `ctl-dir ...` gives the exact path)

## 1. Key path, install to the first prompt (from the 02:42 run's `Native input audit` + FE transitions)
Keys: J = A, K = B, Enter = START, Esc = BACK. The game window must have focus.

| # | FE state / screen | Key | Next | 02:42 timing |
|---|---|---|---|---|
| 1 | 7 install prompt (~30 s after launch) | J | all pads white; the sidecar LOADs batman/gandalf/wyldstyle ~2.5 s later | 02:42:51 -> J 02:44:59 |
| 2 | 0 install + intro | none (Enter/J don't skip it) | 12 by itself after ~184 s | 02:45:18 -> 02:48:22 |
| 3 | 12 title "Press START" | **wait >= 10 s after it appears**, then Enter; no reaction -> Enter again every ~5 s | 58 -> 40 -> 13 | Enter at +53 s worked; the route's START at +3.8 s was ignored |
| 4 | 13 "press A" | J | 35 -> 0 Updates panel | 02:49:36 |
| 5 | 0 Updates panel | J (Store notice), J (OK), K | 17 main menu | 02:49:56 / 02:50:21 / K 02:50:25 |
| 6 | 17 main menu | highlight must be New Game (if it is on Credits: Right once), then J | 34 -> 40 -> 47 save slots | 02:50:52 |
| 7 | 47 slots | J (slot 1) | 49 Confirm | 02:51:16 |
| 8 | 49 Confirm (default Yes) | J | 52 -> 53 -> 54 autosave notice | 02:51:21 |
| 9 | 54 autosave | J | 55 Toypad picture | 02:51:49 |
| 10 | 55 Toypad picture | J | story (FE 0); the **batman prompt starts within ~1 s** | 02:52:12 |

## 2. Each prompt: accepted or not
Order: pad 2 batman (at once), then pad 3 gandalf (~1 min later), then pad 1 wyldstyle (~2.5 min after that).

**Accepted.** In sidecar.out, in order:
1. `prompt <fig> fire 1/4: /...<colours>/ -> pad N in 1.0 s`
2. `remove REMOVE <fig> pad=.. -> hangup-ok [prompt]`
3. `load LOAD <fig> id=.. pad=N index=.. -> hangup-ok`
4. `prompt-done ok <replace|move> <fig> ...`
5. `remove-confirm` / `load-confirm Toypad listener: LOAD -> pad=N`
6. Then **within ~2 s**, no more `toypad Toypad: pad N mode 3 lit <prompt colours>` lines. The C2 pulse stops.
- On screen: the pad light stops flashing that colour and the story goes on. There is no 120 s wait.
- Reference: the 02:42 batman prompt stopped 0.26 s after its LOAD.

**Not accepted:**
- `prompt <fig> fire 2/4` ~15 s after fire 1 (the pad is still pulsing), and the pulsing continues until the failsafe ~120 s after the prompt started.
- Failsafe = the pulse lines stop with no LOAD near them.

**If it fails, check in this order (at fire 2, ~16 s in):**
1. No `fire` line at all: the colours differ from the spec. Copy 2-3 `pad N mode 3 lit XX XX XX` lines from that prompt.
2. `prompt-done FAIL ...`: copy the error text (for example "already on pad").
3. `prompt-done ok` plus `load-confirm`, and it keeps pulsing: the game didn't take the add event.
   - Don't hand-fix it, and don't change the mapping (G4).
   - Let the failsafe run, note the prompt start / LOAD / pulse-stop times, and go on.
   - Hand ctl during the 4 auto fires would race the sidecar.

## 3. After the 3 prompts, in gameplay with player control
Write each file once the previous one is `.done`, about 10 s apart. Example:
`Set-Content -Encoding ascii <run>\toypad-ctl\001.cmd 'status'`

- Each file is taken once it is >= 0.5 s old, then renamed `NNN.done` with the results appended (`NNN.err` = error, in which case stop and report).
- Don't remove all three figures at once: the game would stop and ask for a character.

| NNN | command | .done result line | wait | on screen |
|---|---|---|---|---|
| 001 | `status` | `ok: status -> slots: batman pad=2 index=0, gandalf pad=3 index=1, wyldstyle pad=1 index=2` | 3 s | nothing |
| 002 | `remove batman` | `ok: remove batman -> REMOVE batman pad=2 index=0 -> hangup-ok` | 10 s | Batman leaves (control passes to another character if he was active) |
| 003 | `place batman 2` | `ok: place batman 2 -> LOAD batman id=1 pad=2 ... hangup-ok` | 10 s | Batman joins |
| 004 | `remove gandalf` | `... REMOVE gandalf pad=3 ... hangup-ok` | 10 s | Gandalf leaves |
| 005 | `place gandalf 3` | `... LOAD gandalf id=2 pad=3 ... hangup-ok` | 10 s | Gandalf joins |
| 006 | `remove wyldstyle` | `... REMOVE wyldstyle pad=1 ... hangup-ok` | 10 s | Wyldstyle leaves |
| 007 | `place wyldstyle 1` | `... LOAD wyldstyle id=3 pad=1 ... hangup-ok` | 10 s | Wyldstyle joins |
| 008 | `move gandalf 1` | REMOVE pad=3, then 1 s later LOAD pad=1, both hangup-ok | 10 s | Gandalf leaves and rejoins (same character; pad position only matters in pad puzzles) |
| 009 | `move gandalf 3` | REMOVE pad=1, then LOAD pad=3 | 10 s | same, back |
| 010 | `swap batman wyldstyle` | both REMOVEd, then batman LOAD pad=1, wyldstyle LOAD pad=2 | 10 s | both leave and rejoin |
| 011 | `swap batman wyldstyle` | back: batman pad=2, wyldstyle pad=1 | 10 s | both leave and rejoin |
| 012 | `status` | slots as in 001 | - | - |

- For every REMOVE/LOAD, game.log should show `Toypad listener: REMOVE/LOAD -> pad=N index=M` (sidecar.out: `remove-confirm` / `load-confirm`).
- The real proof is the screen: the character leaves or joins within ~1-2 s.
- A step with listener confirms but no on-screen change = the add/remove event didn't reach the game. Note the NNN and the time.

## 4. Timing (cap 1200 s)
| phase | best | with 2 failsafes |
|---|---|---|
| launch -> 7 install prompt | ~30 s | |
| J -> intro end (12) | ~185 s (t ~ 3:40) | |
| title -> story (steps 3-10 by hand) | ~100-120 s (t ~ 5:40) | |
| batman / gandalf / wyldstyle prompts | ~3.5 min (t ~ 9:15) | +4 min (t ~ 13:15) |
| ctl 001-012 | ~2.5 min (t ~ 11:45) | (t ~ 15:45) |
| margin | ~8 min | ~4 min |

If the story hasn't started by t = 10:00, skip ctl 008-011.
