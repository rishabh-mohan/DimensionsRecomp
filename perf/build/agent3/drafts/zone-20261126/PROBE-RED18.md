# PROBE-RED18 - plan for the all-pads fast red state (draft, M3, for M10 rating)

Status: DRAFT. Nothing in it has run. No live kit file changed. M10 rating 89D0B10B: P0 SAFE; P1/P2 SAFE-IF R1-R3 (manual only); P3/P4 SAFE-IF R4 (ctl); P5 BLOCKED. Rev 2 (06:20) fixes NITs P-N1 (game_ts throughout) and P-N2 (054546 claim) and restates the red-18 timing as "done + ~18 s".

## 1. What we know (evidence)

Source: manual+dump session `build\agent3\gameplay\runs\20261126-051159-gpman-native` (toypad-events.csv 67B070F6..., game.log 316B7F4F..., Overseer keys log 39642F59..., ctl log B5B35726...).

Times are game_ts (game.log, as carried in toypad-events.csv) unless marked "wall": key presses and screenshots have no game_ts (keys log / shot file time, host clock; wall runs ~35-260 ms behind game_ts in this csv).

| time | event |
|---|---|
| 05:19:44.090 wall | last key press (J, keys log). No key input after this. |
| 05:25:41.272 | zone step T0: pad 3 `FF 00 18` speed 15 |
| 05:27:09.140 | ctl 006 `place batman 1`: listener LOAD confirm pad 1 |
| 05:27:09.275 | all 3 pads solid `99 42 0E` speed 15 (zone step done) |
| 05:27:09 | game.log: new content load (shader adopt/dump lines). No text hint. |
| 05:27:13.3 wall | last Overseer screenshot (`shot-...433296`): dark Vorton-like room, vortex/gateway ring, 6 red floor ovals; LEDs still amber |
| 05:27:26.773 | **pads 1, 2, 3 all `FF 00 00` speed 18** (fast red blink): zone done + 17.5 s (T0 + 105.5 s) |
| 05:27:26.773 to 05:31:59.276 (last row; run cap 05:32:17 wall) | red-18 holds on all pads, ~50 rows/min/pad; draws/frame steady 686-687 (static scene) |

- No screenshot exists after the red-18 start, so the HUD text in that state is unknown.
- The state did not clear on its own in ~273 s (game_ts, first to last row) without input.
- `FF 00 00` at speed 15 is a different signal: a zone-step cue on pads 2/1 in some runs (EXPLORE3 045407, session 041246). Speed 18 on all 3 pads at once has been seen only here.
- GAMEPLAY 054546 (no ctl): the zone step was still open at the route stop (pad 3 hint timeout, pad 2 open), and red-18 did not occur before that route's stop. It does not show whether red-18 can come later without the zone rule.

## 2. Hypotheses (ranked by evidence; web sources are AI summaries with no primary source, so low confidence)

- **H1 build/place request (vehicle or gadget).** Early in the starter-pack story, after the vortex intro, the game has the player build a physical model and put it on the pad (web: the LEGO Gateway build in Vorton; another summary says the Batmobile and that the pad "flashes red" when it wants a vehicle). The 6 red floor ovals and the gateway ring in the 05:27:13 shot fit a Gateway/Vorton scene. If the game wants a vehicle tag, we have no vehicle tag, and whether ldtag/the sidecar can make one is unknown. That would need a new tag build plus a rating (P5, blocked).
- **H2 build-instructions screen waiting for a button.** The Gateway build has on-screen instructions paged with A/B. Pads blink red while it waits. A J (A) press would page or close it.
- **H3 text or continue prompt** (a dialogue box, "press A"). Same action as H2.
- **H4 the game wants figures lifted/re-placed** (e.g. "place a character on the pad" after a scene change resets the pad state).

The H2/H3 vs H1/H4 split will most likely come from the P0 screenshots alone.

## 3. P0 - passive (no input; can be automatic)

- Trigger: the first `FF 00 00` speed 18 row on any pad (sidecar `alert` row).
- Screenshots at alert start +5 s, +30 s, +60 s.
  - Unattended runs: the draft `--led-shots` sidecar flag logs `shot` rows `alert<n>-plus05s/plus30s/plus60s`; the draft watcher turns each one into `<arm>-led-<nn>-<label>.jpg` plus an index.csv row with mark `led_<label>` (see ZONE-DRAFT.md, item 3).
  - Manual sessions: the Overseer takes the same 3 shots with cc.ps1.
- Read the HUD in each shot: text box, button glyphs (A/B/Start), build-instruction page, vehicle/gadget icon, "place ... on the Toy Pad" text, pad-outline graphic.
- Record: first/last red-18 game_ts per pad, any LED change between the shots, draws/frame trend (frames.csv).
- P0 alone is enough to choose between H1-H4. Stop there unless a rating clears P1+.

## 4. Action ladder (least risk first; each step needs a rating)

General rules for every step:
- One action at a time, ≥10 s apart. After each one: wait 10 s, take a screenshot, read the toypad-events LED rows.
- Stop the ladder at the first step that changes the LEDs away from red-18, or that shows a menu or screen we don't expect. Report that, don't go on.
- Record the wall time of every action and match it to game_ts (toypad-events) and to the next screenshot.
- No step changes the route or kit files.

| Step | Action | Fits | Risk | Success sign |
|---|---|---|---|---|
| P1 | `J` (A) once | H2, H3 | Low: A in a text/build screen pages or closes it. In free play it is jump/interact. | the screen pages or closes; red-18 stops or changes |
| P2 | `Return` (Start) once. If a pause menu opens, `Return` again to close it (or `K`/B if Return doesn't close it) | pause/skip prompt | Low-medium: may open the pause menu; a second Return closes it (resume is the default item) | a skip/continue prompt appears, or no effect (then go back to the same state) |
| P3 | ctl `remove batman`; ≥10 s later `place batman 1` | H4 | Medium: may start a new pad prompt cycle | pad 1 LED changes on the remove/place; red-18 clears |
| P4 | ctl remove wyldstyle, gandalf, batman (≥3 s apart); ≥10 s later place w 3, g 2, b 1 (≥3 s apart) | H4 | Medium-high: full reset of the pad; may replay the prompt cycle | red-18 clears, normal LEDs per pad |
| P5 | place a vehicle/gadget tag (if H1 is confirmed by the P0 HUD) | H1 | **Blocked**: needs a tag we don't have and an ldtag/sidecar check, then its own rating | n/a |

Hard stops: the game exits, the screen goes black for more than 30 s, a failsafe fires, or an LED pattern appears that is neither red-18 nor a known cue.

## 5. Where it runs

- **Unattended (EXPLORE/GAMEPLAY with the draft `zone` and `--led-shots`):** P0 only. Red-18 is expected at zone done + ~18 s (051159: 17.5 s, game_ts). With the kit's `--zone-delay 45`, done is expected at about T0+55-65 s if the game accepts step 1 (M10 Z-S1), so red-18 at about T0+73-83 s and its +60 s shot at about T0+135-145 s. EXPLORE3's route stopped ~T0+170 s, so the +60 s shot fits before the stop. Without `zone` (3 × 120 s hint timeouts), red-18 would come after the route stop and P0 would not capture it.
- **Manual session (Overseer by hand):** P0 by cc.ps1, then P1 and P2 only if rated, then P3/P4 by ctl if rated. Same zone ctl as the 051154 session to reach the state (zone done + ~18 s).

## 6. What to report after a probe

- Red-18 first/last game_ts per pad; the state after each action (LED rows with game_ts).
- Screenshot paths plus the HUD text read from each.
- Which hypothesis it supports; the next rated step proposed.
