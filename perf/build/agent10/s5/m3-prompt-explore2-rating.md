# Rating: M3 prompt_sidecar + EXPLORE2 delta (RUN-MANUAL, RUN-EXPLORE)

Who/when: M10 (pre-read by E10.2, re-verified by M10), 2026-11-25 ~21:30 local. Static only: user pause active. I ran no kit script and no selftest, only scratch .cmd copies with the launch line removed.

## Files (sha256/16, bytes) - WS\build\agent3\gameplay\ (no kit\ subfolder)

| file | sha256/16 | bytes |
|---|---|---|
| prompt_sidecar.py | 31C33A80A2DC9973 | 23069 |
| selftest_prompt.py | BAA14BFC266D6502 | 10904 |
| selftest\prompt-selftest.txt | A35673CC50899EE1 | 2610 (PASS 25/25) |
| gameplay-run.ps1 | 1F7900B9BCD7400D | 25697 |
| gen_gameplay_route.py | 92629EF35FB7BE6A | 11867 |
| explore-route.txt | D2D7D26D72FAC239 | 7491 (236 steps, 0 tp- marks) |
| gameplay_post.py | E33DF65402DF053C | 17682 |
| RUN-MANUAL.cmd | 1C3F7D8574E90DD5 | 5689 (CRLF, 25 pins) |
| RUN-EXPLORE.cmd | E3F5890BD83789F7 | 5493 (CRLF, 25 pins) |
| RUN-GAMEPLAY.cmd | 5F8D0192B6AA9E52 | 5193 (CRLF, 25 pins; not rated, route stale) |
| WS\build\agent3\toypad\fake_listener.py | 3446BA57 | - |
| delta diff (Overseer scratch) | 4C6D5A30 | - |

Base: m3-manual-kit-rating.md 6A70CF8A (M1-M6; RUN-MANUAL 9AF55219, gameplay-run 06C4134C).

## Verdict: SAFE-IF (C1-C3)

RUN-MANUAL and RUN-EXPLORE are both covered. Hand-written toypad-ctl files during RUN-MANUAL are allowed under the rules in "Toypad ctl rules" below.

## What I checked

- Shas: all match the brief (E10.2, then re-hashed by me).
- Pins: E10.2 re-hashed all 25 pins in RUN-MANUAL and RUN-EXPLORE: 25/25 match. The pin lines are identical across the 3 cmds. All three are CRLF-only, ASCII, with a count check of 25.
  - Coverage: everything the ps1 runs or imports, including prompt_sidecar, selftest_prompt, fake_listener, toypad_sidecar/client/ldtag and the 3 tag .bin files. tags.json is not pinned and no code reads it.
  - Scratch tamper (E10.2, same depth, launch replaced by echo): untouched rc 0 "pins ok: 25"; one hex changed -> 3; fake_listener renamed -> 3 MISSING; extra GPPIN_99 -> 3 (count 26). 4/4.
- gameplay-run.ps1 1F7900B9 (read by E10.2 in full; key lines re-read by me):
  - Lock: still `[IO.File]::Open(logs\gameplay.lock, ..., 'None')`, REFUSED exit 3 (L80-81), taken before the refusals and arms in every mode.
  - `manual` + `explore` -> exit 2 (L49).
  - Seconds: manual 1200, explore 1500, route 900 (L50). Manual has no -InputScript and no watcher (L273).
  - Refusals L117-158 unchanged in content (HOLD, GO, D1, day launcher, running game, active runners, desktop, RAM); exit 3 if not dryrun (L157).
  - Sidecar: Start-Process python, handle held, added to $script:helpers (L268-270). After each arm, WaitForExit 240 s, then Kill (L285-288); on abort the finally calls Stop-Ours (L296-297), which stops helpers by held handles. Same pattern as the old sidecar.
  - Sidecar args: --timeout Seconds+240, --boot starter, 3 --on specs; manual skips --then-mark (L178-183).
- prompt_sidecar.py (read by E10.2 in full; writes/ctl loop re-read by me):
  - Writes: toypad-events.csv (append, L266), os.makedirs(<run>\toypad-ctl) (L278-279), os.replace of ctl files to .done/.err plus an appended annotation (L366-375), and stdout. No subprocess/eval/exec/rmtree in the file.
  - Ctl loop (L327-376): .cmd only, in name order, waits until mtime >= 0.5 s, size <= 4096, <= 20 commands, '#' comments, stops at the first failing command. PermissionError -> return (retried on the next poll).
  - Tags: names ^[a-z0-9_]{1,32}$ -> tags_dir\<name>.bin, so no path traversal. Pads 1/2/3 only.
  - Network: client only, to 127.0.0.1 (port from --port or the game's "127.0.0.1:N" listener line).
  - Lifetime: exits on <run>\summary.json or --timeout.
- D1 guard: no kit file adds window-s5 / run-matrix / RUN-WINDOW strings apart from the guard itself. The new process is python.exe, which the name filter excludes. Synthesized command lines all False (E10.2).
- gameplay_post.py E33DF654:
  - "vortex (level loaded)" moved from HARD to INFO; FE column added; draws/verts n/a on native.
  - Clean-exit/WER/dump gates and the verdict logic are unchanged. This loosens a progress gate only, with no safety effect.
  - Writes only --out. The ps1 calls gen with --check, so it doesn't write.

## Toypad ctl rules (hand-written toypad-ctl\NNN.cmd during RUN-MANUAL)

Allowed. They send no keystrokes. They only drive our game's 127.0.0.1 Toy Pad listener and stay inside our run dir.

- (a) Path: only the exact dir from the `ctl-dir` line in build\agent3\gameplay\logs\<stamp>-native.sidecar.out.txt for the current run. Older run dirs under runs\ are dead.
- (b) When: after the sidecar logs `listener port N` and before the run ends. Files written after summary.json stay unprocessed.
- (c) Names: zero-padded NNN.cmd, increasing, never reused, lowercase .cmd. Never create a directory (or anything else non-file) named *.cmd: it stalls the queue for the rest of the run (N1).
- (d) Atomic write: write NNN.tmp, then rename to NNN.cmd. ASCII/UTF-8 (`Set-Content -Encoding ascii` or [IO.File]::WriteAllText). Do not use `>` / Out-File in PowerShell 5.1: they write UTF-16 -> .err. Close the file before renaming.
- (e) One command per file. Commands, lowercase: `place <tag> <1|2|3>`, `remove <tag>`, `move <tag> <1|2|3>`, `swap <a> <b>`, `replace <tag>`, `status`. Pad 1 = centre, 2 = left, 3 = right.
- (f) Tags: only batman, gandalf, wyldstyle (the 3 pinned .bin files).
- (g) Write nothing else into the run dir. summary.json ends the sidecar; an input.csv with tp-* marks would be executed.
- (h) Check the result (NNN.done/.err, the ctl rows in toypad-events.csv, the game.log "Toypad listener" lines) before the next file. Leave >= 2 s between files.
- (i) Avoid hand commands while a prompt trigger is due (the --on triggers move/replace the same tags). Collisions give harmless "already on pad" errors.

## Conditions

- C1: M1-M6 carry over. The 3 cmds have new shas:
  - RUN-MANUAL needs a fresh dryrun ALL PASS on 1C3F7D85 (send me the log sha) before the next manual session.
  - RUN-EXPLORE needs its own dryrun ALL PASS on E3F5890B before its first run.
  - RUN-GAMEPLAY stays unrated until the route is refreshed and P4 is re-matched.
- C2: hand-written ctl files only as in "Toypad ctl rules" (a)-(i).
- C3: build\agent3\gameplay\tags holds exactly the 3 pinned .bin files (+ tags.json). Add no other .bin files.

## Findings

- SHOULD S1: there's no byte diff for the gameplay-run.ps1 06C4134C -> FE060F86 change (the sidecar wiring). The delta diff omits the ps1, and M3's 21:14 backup already contains the wiring; FE060F86 -> 1F7900B9 is only the header plus L50. The "unchanged" claims rest on a full read plus consistent offsets. M3 should provide the 06C4134C copy or that diff. Not blocking: the lock, refusals, finally and helper kill were read directly.
- NIT N1: a *.cmd directory, or a *.cmd file held open forever, stalls all later ctl files (stat/PermissionError -> return, L338-363). Rule (c)/(d) covers it.
- NIT N2: any [a-z0-9_]+.bin in the tags dir is loadable, and only 3 are pinned. Hence C3.
- NIT N3: a 20-line ctl file can block the main loop for minutes (5 s timeout per LOAD/REMOVE). It's bounded by the ps1's 240 s wait + Kill. Rule (e) says one command per file.
- NIT N4: the @* triggers can fire up to 4x each per run (15 s cooldown). Functional only.
- NIT N5: _remove pops the slot before the network result (L101-104), so the map can desync if a REMOVE fails. Functional only.
- NIT N6: selftest_prompt p.wait(timeout=60) has no kill on timeout, so a hung sidecar lingers up to its 90 s timeout. It writes only selftest\simruns (rmtree at a fixed path).
- NIT N7: ps1 header L19 still says "-Seconds 900".
- NIT N8: toypad_client starter_tags would write missing tags. Unreachable in real runs because of the precondition (L118) and the pins.
