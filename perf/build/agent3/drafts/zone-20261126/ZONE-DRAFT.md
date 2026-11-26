# ZONE-DRAFT - sidecar zone-step rule (C6), LED-state screenshots (item 3), cand5 word - draft rev 2, M3, for M10 rating

Status: DRAFT rev 2 (06:21). Candidate files are in `b\`; `a\` holds unmodified copies of the live S1 files (re-checked 06:20: live = a for all 7). **No live kit file changed.** Install needs an M10 rating, then the Z1 order (section 7).

Update 06:31 (docs only): M10 rated rev 2 SAFE-IF I1-I6 (18509DEB); the 7 b\ files were installed at 06:29 per I2 (live = b). Folded M10 K-N1 (section 8, lock backstop note) and K-N2 (PLAN-proof5 sha, section 9). No b\ file changed.

Rev 2 vs rev 1 (M10 rating 89D0B10B, Overseer 12:12Z / 12:15Z):
- new word `cand5` (M16 proof5, section 9);
- Z-S1: the `zone` word now passes `--zone-delay 45` (kit default; the sidecar's own default stays 25);
- Z-N1: `zone-skips=<n>` in the sidecar result line;
- Z-N2: a `zone` row `prompt after T0: ...` when a prompt fires after T0;
- Z-N3: red-18 timing restated as "done + ~18 s" (section 3);
- the dryrun now checks the exit-2 word combos itself (section 5);
- selftest scenario F (skip + prompt after T0).

## 1. Rule (what the Overseer asked, and how the draft maps it)

| Overseer step | Draft behaviour (`prompt_sidecar.py --zone`) |
|---|---|
| Trigger T0 = pad 3 `FF 00 18` speed 15 after all 3 prompts | `Zone.feed_led`: armed state; needs pad 3, rgb `FF 00 18`, speed 15 and `prompts_done()` (all 3 `--on` prompts answered). Logs `zone-t0` and a shot. |
| ≥T0+25 s: remove gandalf, then move wyldstyle 3 | Step 1 (pad 3 wants wyldstyle) starts at T0 + `--zone-delay`. **The `zone` word passes 45** (M10 Z-S1: the earliest evidenced accept is ~T0+48.5 s; with 25, step 1 + retry could stop at ~T0+55 before the game accepts). Plan = remove every other figure on pad 3, remove wyldstyle if it is on any pad, place wyldstyle 3. For layout b2 g3 w1 that is `remove gandalf; remove wyldstyle; place wyldstyle 3` = "remove gandalf, then move wyldstyle 3" (move = remove + place). |
| on pad 2 slow `FF 6E 18`: remove batman, then place gandalf 2 | Step 2 starts `--zone-gap` after the pad 2 cue. Plan for b2 (g off): `remove batman; place gandalf 2`. |
| on pad 1 slow `00 00 18`: place batman 1 | Step 3 starts `--zone-gap` after the pad 1 cue. Plan: `place batman 1`. |
| Gaps ≥2 s | Commands are queued and non-blocking, `--zone-gap` (2 s) apart. |
| one retry per step, then stop and log | No cue within `--zone-confirm` (10 s) after the last command: one retry (a fresh plan, which re-places the figure); a second miss = `zone-stop`. A failed ctl command: one re-plan; a second failure = `zone-stop`. After a stop the zone does nothing more. |
| Off by default; explicit flag in RUN-EXPLORE/RUN-GAMEPLAY | Sidecar `--zone` (needs `--on`, else exit 2). `gameplay-run.ps1` passes `--zone --zone-delay 45` only with the word `zone` (`RUN-EXPLORE.cmd zone`, `RUN-GAMEPLAY.cmd nativeonly zone`); `zone` with `manual` exits 2. |

Done: all 3 pads `99 42 0E` (speed 15) during step 3 = `zone-done`.

Extra cue (evidence-driven): pads 2 and 1 also accept `FF 00 00` speed 15 as their cue.
- In EXPLORE3 (045407) and session 041246, the pad 2 cue was `FF 00 00` speed 15.
- In 051159 (gandalf on no pad) and in the GAMEPLAY run 054546, it was `FF 6E 18`. In 054546 gandalf stood on pad 3, after the pad 3 120 s hint timeout.
- So the colour is not just "figure on another pad". Accepting both colours makes the rule independent of which one the game picks.
- A later pad's cue while an earlier step is open skips to that step (a `zone` row "... skipping to it"; counted as `zone-skips=<n>` in the result line).

Handoff latency is logged per step on game_ts from our LOAD confirm (falls back to the sidecar clock), e.g. "step 1 pad 3 handoff (pad 2 lit FF 6E 18) 0.065 s after the LOAD confirm (game_ts)".

A prompt that fires after T0 (on-max 4, cooldown) is logged as a `zone` row `prompt after T0: <name> fire <n>/<max> -> pad <p> (zone step <k>, state <s>)`. The prompt is still answered; a resulting ctl error is covered by the zone's one re-plan.

With `zone`, the route's `v-replace` then-mark is not wired (`--then-mark` omitted). It would reshuffle the figures in the middle of the step (EXPLORE3: v-replace at 05:06:42-49 put wyldstyle on pad 3 by chance).

Result line (end of sidecar.out): `... zone=<done | stopped: ... (step k) | armed (step 0) | off> zone-skips=<n> alerts=<n> shots=<n> slots: ...`.

## 2. Evidence the rule is built on

Manual+dump session `runs\20261126-051159-gpman-native` (toypad-events 67B070F6...), all game_ts:
- T0 = pad 3 `FF 00 18` speed 15 at 05:25:41.272.
- 002 remove gandalf (remove confirm 05:26:37.5).
- 003 move wyldstyle 3: LOAD confirm 05:26:41.333 → pad 2 `FF 6E 18` at 41.398 (65 ms).
- 004 remove batman: remove confirm 05:26:58.513.
- 005 place gandalf 2: LOAD confirm 05:27:02.319 → pad 1 `00 00 18` at 05:27:02.383 (64 ms).
- 006 place batman 1: LOAD confirm 05:27:09.140 → pads 1-3 `99 42 0E` speed 15 at 05:27:09.275 (135 ms).
- Then all pads `FF 00 00` speed 18 from 05:27:26.773 (done + 17.5 s; see PROBE-RED18.md).

Other points:
- Before the step-1 handoff no pad 1/2 cue row appears (first pad 2 cue 05:26:41.398), so the "skip ahead" path is not used in the normal case.
- The prompt regexes (`F4 69 16` / `F4 00 16` / `00 00 16`, speed 16) don't match the zone colours, and the alert (speed 18) is ignored by the zone (speed 15 only).

## 3. Item 3 - unattended screenshots of the zone step and the red-18 state

- Sidecar `--led-shots` (passive: no pad action) writes `shot` rows to `<run>\toypad-events.csv`:
  - `zone-t0`, `zone-cue-pad2`, `zone-cue-pad1`, `zone-done`, `zone-stop` (with `--zone`);
  - `alert<n>-plus05s`, `alert<n>-plus30s`, `alert<n>-plus60s` after the first `FF 00 00` speed 18 row (an `alert` row marks the start; a new alert only after 120 s without one).
- Watcher (`gameplay-watch.ps1`) reads the csv by byte offset and shoots `<arm>-led-<nn>-<label>.jpg` per `shot` row, with an index.csv row (mark `led_<label>`, route_t_s empty). `gameplay_post.py`'s `^[^-]+-(\d{3})-` name regex skips these files, so the post needs no change.
- `gameplay-run.ps1` passes `--led-shots` in every explore/route run (not manual). M10: always-on is acceptable.
- Timing (Z-N3):
  - Red-18 is expected at **zone done + ~18 s** (051159: 17.5 s, game_ts).
  - With `--zone-delay 45`, done is expected at about T0+55-65 s if the game accepts step 1. Red-18 then comes at about T0+73-83 s, and its +60 s shot at about T0+135-145 s.
  - EXPLORE3 stopped ~T0+170 s. GAMEPLAY 054546 had T0 at route t≈702 s and stopped at t=880 s (T0+178). Both fit.
  - Without `zone` (3 × 120 s hint timeouts), red-18 comes after the route stop. In 054546, pad 2 was still open at the stop.

## 4. Files a → b

| File | a (live S1) | b (candidate, rev 2) | Format |
|---|---|---|---|
| gameplay-run.ps1 | 28F7785BDB47FBDFCA0397BD0139AF5D82BB1EF9D28FFD1298C98CBAD09271BA | 691B70ADA6C5583987CD190BC8D154BAA41C57D204D591D86CB46499E0D5AC24 | LF, no BOM, ASCII |
| gameplay-watch.ps1 | 2950A4471C1271BCDAC132816D89CF3C95812785AF7A569A94850E6A1A3DE068 | 4BE7E90E16F08AAA5C7E069442DF8F602E79385FE287A5FA3FD4BD9521A1F776 (unchanged since rev 1) | LF, no BOM |
| prompt_sidecar.py | 31C33A80A2DC997304B32454750406754B811F6ED640170B1CC4CA613296C504 | 1D9A6EB54B3C300AF0FEB57E266AAD072B272C808CC6087FD47CA2F39A194A4B | LF, no BOM |
| selftest_prompt.py | BAA14BFC266D6502995FF7827363FFB5EBD8CC8734EEF37769DE5F00AB12356F | A48065480D3299B5C2AD60A3E1A814B9112F3606B413174370A824F1F13B9547 | LF, no BOM |
| RUN-EXPLORE.cmd | 5B4A31A98F52F74C5510D3D4DB19ABB6F695F787A0F52C245D93D9E6913681BC | 5B05E10FEF89EF562515443595977171D968B3D56C95064E9E99C8B6C7B33BF3 | CRLF ASCII; rem lines 7-9 (`zone`, T0+45); pins 01/02/23/24 |
| RUN-GAMEPLAY.cmd | 09304AC0606A3EED2DE3C66718463CE3C7CD6C72E4D080E3A436D56467436CD6 | B2B2BE248085E167FD1F2131F40871F380627F4D02599B28B33059FEE54C17EF | CRLF ASCII; rem lines 7-10 (`zone`, T0+45, `cand5`); pins 01/02/23/24 |
| RUN-MANUAL.cmd | DC22DF4FCF57BF899C522521E318E79A623CD67F396C88A4E54D98BA1E739D70 | 6A0AEECAF97BF6433D91F08C657E925BC368E5BE83443EC423B691C03ACA03C8 | CRLF ASCII; pins 01/02/23/24 only |

- The b .cmd pins were checked against the b files plus the live unchanged files: 25/25 match in each .cmd. CR = LF counts (57/56/57), 0 non-ASCII bytes.
- cand5 adds no .cmd pin: the native5pack MANIFEST sha is pinned inside gameplay-run.ps1 (as native4bp's is), and the run refuses on a MANIFEST mismatch or a verify-bins FAIL.
- Unchanged and still pinned: gameplay_post.py, gen, both routes, tags, toypad/*, harness/*, verify-bins, xinput, fake_listener.

## 5. Self-tests (no game, no install)

Test tree: a scratch copy of the b files plus `tags\`, with `toypad\` copies alongside (the layout the kit's relative imports expect).

- `python -B selftest_prompt.py` (rev 2 sidecar + selftest): exit 0, **RESULT: PASS (0 failed)**, scenarios A-F.
  - A-C as before: boot, prompts, ctl, route marks, bad --on, and "--zone without --on prompts → exit 2".
  - **D** (zone 3→2→1 with one retry on pad 2, `--led-shots`, speed-18 alert):
    - no zone action on a pad 3 cue before the prompts are done or at the wrong speed;
    - step 1 runs 3 commands; step 2 is remove batman + place gandalf 2, then one retry; step 3 is place batman 1;
    - 17 listener actions; result `zone=done zone-skips=0 alerts=1`;
    - shot rows `zone-t0 zone-cue-pad2 zone-cue-pad1 zone-done alert1-plus05s`.
  - **E** (no handoff): place wyldstyle 3, then the retry (remove + place), then `zone=stopped`; no action after the stop; 0 shot rows without `--led-shots`.
  - **F** (new): the Batman prompt fires again after T0 → zone row `prompt after T0: batman fire 2/2 -> pad 2`; the pad 1 cue while step 1 is open → forward skip to step 3 (remove batman, place batman 1); 6 listener actions; result `zone=done zone-skips=1`, `prompts=batman:2/2`.
- `gameplay-watch.ps1 -SelfTest` under PS 5.1 (rev 1, file unchanged): exit 0, "SELFTEST led shot rows 2 (zone-t0 alert1-plus05s)", SELFTEST ok.
- `preflight-parse.ps1` (PS 5.1 parser) on b\gameplay-run.ps1 and b\gameplay-watch.ps1: 0 errors.
- Word checks, run directly against b\gameplay-run.ps1 under PS 5.1 (all exit in the word checks, before the lock, python or any file work; no logs dir was created). Each exits 2 with its message:
  - `zone manual`;
  - `cand5 manual nativeonly`, `cand5 explore nativeonly`, `cand5 manual dump nativeonly`, `CAND5 Manual`;
  - `cand5`, `cand5 dryrun`, `cand5 nativeonly xenosonly`;
  - `dump`, `bogusword`.
- Arm/tag/fp logic (scratch `cand5-logic.ps1` evaluates the b lines from `$allArms` to `$wiringFp` plus `$tagBase` and the trace line, no I/O):

| words | pinned | copy | MANIFEST | tag | trace | post fp |
|---|---|---|---|---|---|---|
| nativeonly | native4bp-bin | bin-native | C5181520 | gp-native | trace-native-STAMP | 39129c4c059be5f0 |
| nativeonly cand5 (also + zone) | native5pack-bin | bin-native5 | 787CD694 | gp5-native | trace-native5-STAMP | a349d5292f67b127 |
| explore | native4bp-bin | bin-native | C5181520 | gpexp-native | trace-native-STAMP | 39129c4c059be5f0 |
| manual | native4bp-bin | bin-native | C5181520 | gpman-native | trace-native-STAMP | 39129c4c059be5f0 |
| (none) | native4bp + devfinal2 | bin-native, bin-xenos | C5181520, 4A4A13ED | gp-native, gp-xenos | trace-native/xenos-STAMP | 39129c4c059be5f0 |

  The dryrun's native wiring check uses `$wiringFp` = 39129c4c059be5f0 in every case (M16's native4bp smoke run is the stand-in).
- `prompt_sidecar.py --help`: contains `--zone `, `--led-shots` and `--then-mark` (the strings the dryrun help check matches).
- Added to the dryrun itself: it runs the exit-2 combos above (`zone manual`, `cand5 manual nativeonly`, `cand5 explore nativeonly`, `cand5 manual dump nativeonly`, `cand5`, `cand5 nativeonly xenosonly`, `dump`, `bogusword`) as child `powershell -File gameplay-run.ps1 <words>` and counts any exit other than 2 as a failure. The children exit before the lock (a child that reached the lock would get exit 3, which counts as a failure).

## 6. Diff

`zone.diff` (`git -c core.autocrlf=false diff --no-index --output=zone.diff a b`, run in this dir; 7 files, +449/-37; no profile paths): sha256 27A33CB3EA8153734AC8EEBF01E0AAC468C91F81FF39A9D16D857CA600E8DBCB

## 7. Install and dryrun plan (M10 Z1; after the rating; Overseer queues)

1. Install the 7 b files into `build\agent3\gameplay\` (gameplay-run.ps1, gameplay-watch.ps1, prompt_sidecar.py, selftest_prompt.py, RUN-EXPLORE.cmd, RUN-GAMEPLAY.cmd, RUN-MANUAL.cmd). The b .cmd files already carry the b pins.
2. Re-check pins 01/02/23/24 in all 3 .cmd (set-pins only if a sha differs; no cand5 pin).
3. PS 5.1 parse.
4. Tamper test per .cmd (pincheck exit 3 on a changed byte, 0 when restored).
5. Dryruns, one at a time:
   - `RUN-EXPLORE.cmd dryrun zone`: the ZONE line (`--zone --zone-delay 45`); the SIDECAR line has `--led-shots --zone --zone-delay 45` and no `--then-mark`; "then-mark/then-action/on/zone/led-shots flags present"; prompt self-test exit 0 (A-F); watcher self-test ok; 8 "word combo ... (expected 2: ok)" lines; DRY RUN ALL PASS.
   - `RUN-EXPLORE.cmd dryrun`: SIDECAR line has `--led-shots` and the v-replace then-mark, no `--zone`; ALL PASS.
   - `RUN-GAMEPLAY.cmd dryrun nativeonly zone`: as the first, tag gp-native; ALL PASS.
   - **`RUN-GAMEPLAY.cmd dryrun nativeonly cand5`** (HEAVY: copies + hashes native5pack-bin, 9 files, 382,516,369 bytes, into a new `bin-native5`; `bin-native` untouched). Expect:
     - a `CAND5: native arm = ...native5pack-bin (MANIFEST 787CD694F0B884D9), copy ...bin-native5, tag gp5-native, trace trace-native5-<stamp>, post --expect-fp a349d5292f67b127` line;
     - `native pinned MANIFEST sha256 787CD694F0B884D9 = pin`, verify-bins PASS on native5pack-bin, then on bin-native5 after the copy;
     - COMMAND line with `-BinDir ...\bin-native5`, `-Tag gp5-native` and `LEGO_NATIVE_TRACE_DIR=...\trace-native5-<stamp>`;
     - SIDECAR line with `--tag gp5-native`, `--led-shots` and the v-replace then-mark (no `zone` word);
     - post native wiring ok (still 39129c4c with the M16 smoke stand-in);
     - DRY RUN ALL PASS.
   - `RUN-MANUAL.cmd dryrun`: no `--led-shots`, no `--zone`; ALL PASS.
   - Must exit 2 (cheap, before the lock): `RUN-MANUAL.cmd dryrun zone` ("not allowed with 'manual'"), **`RUN-MANUAL.cmd dryrun cand5`** and **`RUN-GAMEPLAY.cmd dryrun manual cand5`** ("'cand5' is not allowed with 'manual', 'explore' or 'dump'"), `RUN-EXPLORE.cmd dryrun nativeonly cand5` (explore).
6. Send every sha and the dryrun log shas to M10 (the dryruns get their own rating). Nothing else runs during install and dryruns; G1: no xenos.
7. Real run candidates, each with its own GO (Z2, X1 hands off, ctl=0): `RUN-EXPLORE.cmd zone` (native default) or the proof5 run `RUN-GAMEPLAY.cmd nativeonly cand5` (M16 PLAN-proof5). The ZONE / CAND5 lines and the sidecar args in the run log must match the dryrun.

## 8. Risks / open

- Blind route keys during the zone step (X3) may move the camera or start a dialogue; the zone only acts on the pad, so it does not fix that.
- The cue colour (`FF 00 00` vs `FF 6E 18` at speed 15) varies between runs (045407 / 041246 vs 051159 / 054546). The rule accepts both; the cause is unknown.
- A prompt after T0 (not seen yet) and a zone plan could overlap on the pad; it is now logged (`prompt after T0`), and the zone's one re-plan covers a ctl error.
- The route may stop before the zone step finishes if T0 comes late. The zone stops with the sidecar (`--timeout`).
- `--zone-delay 45` is untested against the game: if the game accepts only later than ~T0+69 s (45 + gap + 10 s confirm + retry + 10 s), step 1 still stops; treat a step-1 stop as inconclusive (M10 Z-S1).
- The tests use a fake listener: real game timing is checked only by the first real run.
- M10 K-N1: the dryrun's word-combo self-runs (child `powershell -File gameplay-run.ps1 <words>`) rely on the parent holding `logs\gameplay.lock` as a backstop: a child that got past the word checks would hit the held lock and exit 3, which counts as a failure. A comment saying so goes into the next ps1 revision; the installed rev 2 ps1 (691B70AD) is not changed for it.
- Z3 post items (T0, per-step commands/confirm/latency/retry/skip/stop, zone= state, shot rows, alert first/last per pad) are read from toypad-events.csv by hand in the M3 post; `gameplay_post.py` is unchanged.

## 9. cand5 (M16 proof5; Overseer 12:12Z)

- Purpose: M16's miss-count proof run on the rebuilt bin (`build\agent16\proof5\PLAN-proof5.md`: M10 K-N2 cites FD5C68CF (rev 2 cited B4E68499); re-hashed 06:31 it is 5EF603B2, last written 06:29:32 by its owner, so cite the current sha when you use it).
- Allowed only with `nativeonly`. Exit 2 with `manual`, `explore` or `dump`, without `nativeonly`, or with `xenosonly`. All checks run in the word checks before the lock.
- With it:
  - native arm pinned = `build\agent16\pack\native5pack-bin`, MANIFEST sha256 787CD694F0B884D99D1D1E3C807642B33CBA22D79A8F9253C071A8898D1446A1 (checked 06:14: file matches; it lists legodimensions.exe 90BF6B4552217E71E437D2BA7976D49EEA30AB3D8EE42B21B6A20E58A2F7EE7D, which verify-bins checks);
  - copy `build\agent3\gameplay\bin-native5` (`bin-native` untouched);
  - run tag `gp5-native` (run dirs `<stamp>-gp5-native`; the watcher filter `*-gp5-native*` and the run-dir filter `*-gp5-native` don't match gp-native and vice versa);
  - trace dir `trace-native5-<stamp>`;
  - post `--expect-fp a349d5292f67b127`;
  - a `CAND5:` log line; LATEST.txt says `route cand5`.
- The arm stays named `native`, so the post's `--arm native=...` and "native fingerprint" check work unchanged.
- Without the word nothing changes (native4bp-bin, bin-native, gp-native, trace-native-<stamp>, 39129c4c); see the table in section 5.
- cand5 can be combined with `zone`.
