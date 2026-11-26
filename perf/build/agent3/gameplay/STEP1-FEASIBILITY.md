# Gameplay route: Step 1 feasibility (M3, 2026-11-25 18:05)

Verdict: **GO (conditional)**. Input and Toypad are scriptable today with no code change. A fresh sandbox profile reaches level load. The open question is player control after the post-load "vortex" scene. The first run after 20:15 has to be a visible exploration run with screenshots; expect 1-2 iteration cycles.

## a) Input: supported, no diff needed
- `harness\vpad\vpadhost.cs` grammar, L7-22:
  - waits: `wait_first_frame`, `wait_perf_rows`, `wait_log "regex" [t]`, `wait_scene`, `wait_change`
  - control: `sleep S`, `mark`, `stop`, `connect`
  - input: `press BTN[+BTN] [count] [hold_ms] [gap_ms]`, `hold BTN[+BTN] MS`, `stick L|R X Y MS` (-32768..32767, recentres after MS), `trigger L|R V MS`
- Buttons: A B X Y START BACK UP DOWN LEFT RIGHT LB RB LS RS GUIDE. Combos use `A+B`. Only slot 0 is driven. The xinput dll already maps the sticks (WritePad L246-261).
- Limits:
  - Steps block and run one after another (Exec L384-403), so walking and attacking can't overlap. The route alternates stick and press steps instead.
  - There is no loop construct, so a python generator unrolls the route.
  - `wait_scene` and `wait_change` return n/a in the real game (perf.csv is opened unshared, L12-13 and L120-121). Use `wait_log` on game.log.
- Optional diff, only if walking and attacking must overlap: a non-blocking `stick_set`/`release` in a copy of vpadhost.cs. run-game loads `$PSScriptRoot\vpad\vpadhost.cs` (L169), so this also needs a copied run-game.ps1 plus its deps in gameplay\. Not proposed for now.
- The kit uses the pinned `build\agent3\vpad\xinput1_4.dll` read-only and modifies nothing under `build\agent3\vpad\`.

## b) Toypad: scriptable, no source change
- `rexglue-sdk/src/input/portal/emulated_toypad.cpp`: TCP listener on 127.0.0.1:9191 (HandleCommand L872-966, port from env REXGLUE_TOYPAD_PORT).
  - Commands: 0x01 LOAD (180 B tag), 0x02 REMOVE, 0x03 MOVE, 0x04 GET_LED.
  - Pads: 1 = centre, 2 = left, 3 = right; index 0-6.
- cvar `toypad_emulation` defaults to true (input_system.cpp L38-40). No figure is placed automatically.
- Existing tooling in `build\agent3\toypad\` (mine, reused read-only):
  - `toypad_client.py`
  - `toypad_sidecar.py`: tails game.log, triggers on a log line or a route `mark`, then place/remove/replace; writes toypad-events.csv
  - `ldtag.py` tag generator
  - generated tags: `tags\batman|gandalf|wyldstyle.bin`
  - selftests: `selftest_toypad.py --cpp` 45/45 PASS
- The 11-22 runs logged "figure added" events, and REMOVE followed by a re-LOAD worked.
- Tag data is generated from public figure ids. No user or Warner data is copied.
- Optional in-process `toypad_script` cvar diff (~60-80 lines): not needed.

## c) Saves: no playable save on this PC; none needed
- Saves go to `<user>\B13EBABEBABEBABE\5752084B\00000001\...`.
- run-game gives each run its own `<run>\user` (or `-UserDir`), so every run starts from a fresh sandbox profile and the user's real data is never touched.
- No run has ever written a story save.
- README L334-335: quitting before the opening cutscenes finish can leave an unloadable save. A per-run fresh profile avoids depending on one.
- Legal: only the user's own disc install, plus tags generated locally. Nothing is downloaded.
- Details: `research\save-notes.md`, `research\toypad-notes.md`.

## d) Route design and robustness
The base is `build\agent3\toypad\routes\level-l.txt` (119 steps). s4b20 and s4bL0 reached the vortex 119/119.
1. Boot: `wait_first_frame`, sleep 50, START, A.
2. `wait_log "Toypad: pad 3 mode 1 lit FF FF FF"` (front end). The sidecar places Batman, Gandalf and Wyldstyle 2 s later, then `wait_log "Toypad listener: LOAD -> pad=3"`.
3. A presses until `wait_log "lit 99 42 0E"` (story start), then `wait_log "pad 1 mode 3 lit FF 6E 00"`.
4. Level load: 110-155 s of heavy 3D.
5. "Vortex" scene: static 766 draws, LEDs cycling a rainbow.
6. **Unknown:** player control after the vortex.
   - In lx2, A/B/X/Y/RB/LB/RT/LT/dpad/stick/BACK changed nothing.
   - START then A gave new geometry (possibly a pause menu or a skip).
   - The scene may be the Gateway build sequence, which could be skippable or might need a figure prompt.
7. Proposed walk/fight loop, ~3-5 min:
   - stick L N/E/S/W for 1.5-2.5 s each
   - `press X 3 150 250` (attack)
   - `press A` (jump)
   - `hold B 2000` (build)
   - `stick R` (camera)
   - `mark` at each checkpoint, which triggers a screenshot

Robustness:
- Boot through level load is **high**: it is driven by `wait_log` and has been reproduced several times.
- The vortex exit and the walk loop are **unknown** until one visible run with screenshots. The loop itself is timing-tolerant: blind stick and attack input doesn't depend on exact frames.
- No level-name log line exists. "Native distance: loaded level" did not fire.

Planned checks:
- in-level: vortex LED line, then draws above 600 after it, then route steps done
- stalls: frames over 100 ms
- missing draws: native via `LEGO_NATIVE_TRACE_DIR` draw_missing_*; xenos n/a
- screenshots: mark-triggered window capture, as in row3-watch

## Proposal
- First run after clearance: an exploration run on one arm (native).
  - Take the level-l path.
  - At the vortex, try a sequence of START, A, B and figure re-place steps, with a mark and screenshot about every 10 s.
  - Then run the walk/fight loop.
- Fold the findings into the route, then run both arms.
- Alternative: run the best-guess route on both arms directly. It costs the same but risks two runs stuck at the vortex.
