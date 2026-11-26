# Post: manual Toypad debug session 20261126-041246-gpman-native (M3)

**Run:** `build\agent3\gameplay\runs\20261126-041246-gpman-native`
- Kit: RUN-MANUAL 2B60C24F, no args, native4bp, cap 1200 s.
- Waiter END 04:33:06, exit 0.
- The Overseer drove it by hand. Read-only analysis; nothing was changed.

## Evidence

| File | sha256 |
|---|---|
| toypad-events.csv | 73E7AC5EFC29232DE9EF96E381723BA01B171B8739E135ABE41B9B518B77A434 |
| game.log | 0B573C2F700712EC832300FBE5156F3221142B3AC618CAE58583165CEC22766F |
| frames.csv | B4ED6D343D6EF27520775B79BF5B884F8F9B59066127F03B800AE18807BA9E04 |
| summary.json | 5AB6B7F6ACDAE0210C1CCB1CBF6739BBD8773C60DF614C9272C7CE383317B804 |
| gameplay log | 517804DEF744441A05D05ACC50309AEC2F5C2EAE2231430E897555C1E5AD5920 (Overseer) |
| sidecar.out | 4E2F4F27372B7036705C94D0E0A35A9FE05A7E42CA25E54631908656D9E50D1A (Overseer) |
| Overseer ctl-seq.log / manual-keys.log | FBC0AE7F… / 0096A79D… |
| M16 render note | `build\agent16\pack\NOTE-white-portal-0428.md` 015E334BFDB1E8096669FE49E27B783134197B915129BF0560586C2FEEE831A3 |

## 1. Title and menus (hand-driven)

- **Title appears.** fe 12 at 04:17:12.2.
- **First accepted Enter.** Pressed ~04:17:28, accepted 04:17:31.4 (12→58→40→13), **+19 s** after fe 12. This joins the accepted samples +28.6 / +53 / +176 / +1067 s; an Enter at +3.8 s was ignored.
- **State 13.**
  - START/Enter does nothing: at 04:17:53.854 there was no transition after ~5 s.
  - **A (J) at 13 → 0 (Updates)**, at 04:19:44.
- **Route to story.**
  1. J at 13 → 0.
  2. J, J, K → 17 (04:20:37).
  3. J (New Game) → 47.
  4. J → 49.
  5. J (confirm) → 52/53/54.
  6. J → 55.
  7. J (Toypad picture) → story (state 0) at 04:22:16.9.
- This matches the installed title gate: one START per try, the gate on fe 5 pending=0, then A.

## 2. Story prompts: 3/3 auto-answered on fire 1/4, no failsafe

| Figure → pad | Prompt fire (LED spec matched) | prompt-done | load-confirm |
|---|---|---|---|
| batman → 2 | 04:22:17.189 (`00 00 16\|00 00 05`) | 04:22:19.232 replace | 04:22:19.487 |
| gandalf → 3 | 04:23:15.331 (`F4 69 16\|3D 1A 05`) | 04:23:17.385 move 1→3 | 04:23:17.639 |
| wyldstyle → 1 | 04:25:32.725 (`F4 00 16\|3D 00 05`) | 04:25:34.775 move 3→1 | 04:25:35.029 |

- **No fire 2/4.** The result row reads `prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1`.
- **Slot layout after the prompts:** batman 2, gandalf 3, wyldstyle 1.
- **LED grammar** of each story prompt:
  1. All pads go amber `99 42 0E` (speed 15).
  2. The target pad lights in the figure colour at speed 3: batman `00 00 18`, gandalf `FF 6E 18`, wyldstyle `FF 00 18`.
  3. A speed-16 pulse follows. This is what the sidecar matches.
  4. After LOAD, the pads hold steady speed-33 colours.

## 3. ctl 001-016: all DONE, each with a matching listener confirm, 0 err

| ctl | done | command | LED / game reaction |
|---|---|---|---|
| 001 | 04:26:49 | status | b2 g3 w1 |
| 002 | 04:26:59 | remove batman | none |
| 003 | 04:27:09 | place batman 2 | none |
| 004 | 04:27:19 | remove gandalf | none |
| 005 | 04:27:29 | place gandalf 3 | none |
| 006 | 04:27:39 | remove wyldstyle | none directly (see §4: the 04:27:45 amber is the cutscene end) |
| 007 | 04:27:49 | place wyldstyle 1 | none |
| 008 | 04:28:00 | move gandalf 1 | inside the scene load (04:28:00-04:28:39) |
| 009 | 04:28:10 | move gandalf 3 | inside the scene load |
| 010 | 04:28:22 | swap batman wyldstyle (b1 w2) | inside the scene load |
| 011 | 04:28:32 | swap batman wyldstyle (b2 w1) | inside the scene load |
| 012 | 04:28:39 | status | b2 g3 w1 |
| 013 | 04:30:23 | remove gandalf (pad 3) | none (pad 3 had already gone solid at 04:30:15) |
| 014 | 04:30:28 | place gandalf 3 | none |
| 015 | 04:31:00 | remove batman (pad 2) | **pad 2 blink changed from red fast to `FF 6E 18` slow, 0.0 s after the remove-confirm** |
| 016 | 04:31:03 | place batman 2 | **pad 2 changed back to red fast, 0.25 s after the load-confirm** |

- The ctl path works mechanically: remove/place/move/swap/status all landed, and the game saw every change.
- 001-007 ran during the intro cutscene. 008-011 ran inside the 04:28:00-04:28:39 scene load.

## 4. The white portal and the red blink: a scripted Toy Pad step, not a stall

**The game was alive and rendering.** This is from M16's note (015E334B):
- From 04:28:30 to 04:32:40, every frame had ~390-450 draws at 42-49 fps, and the count kept changing (animation).
- The scene loaded 04:28:00-04:28:39. After that there were 0 PSO creates.
- Every frame dropped exactly 3 draws to missing shaders: VS A7FA6E00 / A7FA8990 and PS A7FA6C00 / A7FA8750 / A8302100 (new), plus AC53D0AC / AC49B8F8.
  - The white/static look may come from one of those dropped draws, for example a portal/composite pass. That is unproven.
- game.log stays silent about these misses because its warning budget ran out at 04:17:31.

**Timeline.** From game.log and toypad-events.csv:
1. **04:27:45.405:** `Native scene teardown` skins 196-215. The intro cutscene ends.
2. **04:27:45.62:** 0.2 s later, all pads go amber `99 42 0E` at speed 15, the same pre-step pattern the story prompts use. Before the gandalf prompt the order was the same: teardowns at 04:23:14, then the prompt.
   - So this amber is the **cutscene end**, not ctl 006. 006 was 6 s earlier, and 002-005 caused no reaction.
3. **04:28:00-04:28:39:** the next scene loads (M16).
4. **04:28:14.09:** teardowns of skins 216-218.
5. **04:28:14.66:** all pads go off. **Pad 3 starts a slow blink, `FF 00 18`/off, 1.26 s per phase.**
6. **04:30:15.28:** **pad 3 goes solid `FF 00 18`** (no later pad-3 rows). **Pad 2 starts a fast red blink, `FF 00 00`/off, ~0.5/0.75 s.**
   - No ctl ran between 04:28:39 and 04:30:23, so the game made this change on its own.
   - The Overseer tied it to 013/014, but it came 8 s **before** 013.
7. **04:31:00-04:31:04:** a presence test on pad 2 (015/016).
   - Empty pad 2 → slow `FF 6E 18` blink.
   - Batman back on pad 2 → fast red again.
8. **04:32:15.23:** **pad 2 goes solid `FF 6E 18`** (no later pad-2 rows). **Pad 1 starts the fast red blink** (wyldstyle was on it) and keeps it until the log ends at 04:32:47.

Every 120 s (04:28:14, 04:30:15, 04:32:15) the game moves to the next pad, 3 → 2 → 1. Each time, the previous pad freezes **solid in a figure colour**.

**Identification.** It's a "put the right figure on the flashing zone" Toy Pad step. The data fits one target layout:

| Pad | Wanted colour | = story colour of | Figure there at the time | Pad shows |
|---|---|---|---|---|
| 3 (04:28:14) | `FF 00 18` | **wyldstyle** | gandalf | slow `FF 00 18` (see anomaly) → solid after 120 s |
| 2 (04:30:15) | `FF 6E 18` | **gandalf** | batman | fast red; empty → slow `FF 6E 18`; solid `FF 6E 18` after 120 s |
| 1 (04:32:15) | (predicted `00 00 18`, **batman**) | batman | wyldstyle | fast red until the end |

- **Slow blink in a figure colour** = "this zone wants figure X". **Fast red** = "a figure is on this zone, and it is the wrong one."
- **Solid** = the 120 s hint timer ran out, so the colour stays as a hint and the game moves on to the next zone. Solid is not acceptance: the wrong figure was still on the pad.
- **The target layout is wyldstyle 3, gandalf 2, batman 1**, a 3-cycle away from the layout the prompts left (b2 g3 w1).
- **The HUD head icon agrees:**
  - The Wyldstyle head appeared while pad 3 wanted wyldstyle (seen ~04:28:22).
  - The Gandalf head appeared while pad 2 wanted gandalf (seen after 013/014; it probably switched at 04:30:15).
  - 015/016 caused no icon change, because gandalf was still wanted.
  - **Prediction:** a Batman head after 04:32:15. Please check the screen notes or screenshots if there are any.
- **Anomaly:** pad 3 blinked slow (the "empty" pattern) even though gandalf was on it.
  - Likely cause: 008/009 moved gandalf 3→1→3 at 04:28:00-10, inside the scene load, so the step may have started with a stale zone map.
  - This is the main reason to keep ctl out of loads and cutscenes.
- **The sidecar did not answer this step, as designed.** Its `--on` specs (`$onSpecs`, gameplay-run.ps1 L67 in the live 28F7785B; L66-67 in D97C9228) match only the speed-16 story pulse. This step uses speed-15 `FF xx 18` / `FF 00 00` blinks.
- The white frame is the scene behind the step (rendered, ~400 draws, 3 dropped). Whether it is supposed to look white can only be settled by a snapshot (`LEGO_GPU_SNAPSHOT_DIR`) or a Xenos reference image (M16). It isn't the cause of the wait.

**Confidence.**
- **Facts:** the step is game-driven, sensitive to figure presence, and on a 120 s timer.
- **High:** it's a figure/zone step.
- **Medium:** the exact target layout. It rests on the colour match plus the icon, and we never saw an accept.

## 5. Recommended ctl plan for the next manual session (no dump)

1. **Time.** Story started at 04:22:17 (+571 s) and the step at 04:28:14 (+928 s), which left only 272 s of the 1200 s cap.
   - Use the known key path (§1) to reach the story sooner.
   - Run **no ctl tests before the step.** 001-012 aren't needed again; the ctl mechanics are proven.
2. **No ctl during cutscenes or loads.**
   - Wait for the all-pad amber at the cutscene end, then for the speed-15 blink to start.
   - Or wait until the character visibly moves under hand input.
3. **At the step**, assuming the prompts left b2 g3 w1 again (check with `status` first):

| NNN | command | expected .done | expected LED / screen | wait |
|---|---|---|---|---|
| 001 | `status` | b2 g3 w1 | none | 3 s |
| 002 | `remove gandalf` | REMOVE pad 3 + confirm | pad 3: slow `FF 00 18` (empty, wants wyldstyle) | 5 s |
| 003 | `move wyldstyle 3` | REMOVE pad 1 + LOAD pad 3 | **pad 3 stops blinking or goes solid; the next zone (pad 2) starts blinking** = accepted | 10 s |
| 004 | `remove batman` | REMOVE pad 2 | pad 2: slow `FF 6E 18` (wants gandalf) | 5 s |
| 005 | `place gandalf 2` | LOAD pad 2 | pad 2 accepted; pad 1 blinks (wants batman, predicted `00 00 18`) | 10 s |
| 006 | `place batman 1` | LOAD pad 1 | pad 1 accepted; the step ends: blinks stop, the scene changes or control returns | 15 s |

   - **If 003 doesn't stop pad 3's blink within 10 s:**
     - Note the colour.
     - Try `remove wyldstyle` / `place wyldstyle 3` once.
     - If that fails too, my target-layout hypothesis is wrong. Record it and don't churn.
   - **If the step has already moved on to pad 2 (red),** start at 004.
   - Note the head icon after each line.
4. Only after the step is cleared and control returns, re-test remove/place/swap in free play. If you use the plan's ctl tests, space them ≥10 s apart.
5. **Candidate for later, rated first:** a sidecar `--on` rule for the speed-15 zone step. Map the slow `FF 00 18` / `FF 6E 18` / `00 00 18` blink on pad P to wyldstyle / gandalf / batman, and answer with `move <fig> P`. Only once 3. confirms the layout.

## 6. Known issues

- summary.txt "median draws per 10 s: 0" reads perf.csv `draw_calls`, which is dead on native. The live counter is frames.csv (run median 245). This is a post/summary bug, not fixed now (M16 §4).
- Three new missing shaders are in the portal scene (M16 §3). They are candidates for the story-dump target list.
