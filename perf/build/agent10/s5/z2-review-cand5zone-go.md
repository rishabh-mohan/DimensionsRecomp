# Z2 zone run review + cand5 zone GO

- Who/when: M10, 2026-11-26 07:29. Read-only.
- Base: `s5/proof5-result-zone-go.md` EE9C2C33 (Z2 GO, ZG1-ZG7); `s5/m3-zone-draft-rating.md` 89D0B10B (Z3, PROBE P0-P5); `s5/kit-rev2-install-check-proof5-go.md` 1456CB47; `s5/proof5v3-rerate.md` 63A96A74.

## Files (sha256/16, hashed by M10)

| File | sha256/16 |
|---|---|
| build\agent3\gameplay\post\gameplay-route-20261126-070554.md | E8AD7774BB9C1E96 |
| build\agent3\gameplay\logs\gameplay-20261126-070554.txt | B161B7916F727FF7 |
| build\agent3\gameplay\logs\20261126-070554-native.sidecar.out.txt | 49D010E5DD6A42BB |
| build\agent3\gameplay\post\gameplay-20261126-070554.txt | B0AAEBB013613E8F |
| build\agent3\gameplay\runs\20261126-070559-gp-native\toypad-events.csv | 8C38B18F2D1A6BA8 |
| build\agent3\gameplay\gameplay-run.ps1 (live) | 691B70ADA6C55839 |
| build\agent3\gameplay\RUN-GAMEPLAY.cmd (live) | B2B2BE248085E167 |
| build\agent3\gameplay\prompt_sidecar.py (live) | 1D9A6EB54B3C300A |

## Verdict

- Z2 zone run 070554: **CONFIRMED**. zone=done, first try on all 3 steps; Z-S1 (delay 45) is conclusive.
- ZG3: **holds by equivalent evidence**. The wording gap is mine: ZG3 asked for a line that only dryruns print.
- PROBE P0: the Overseer's reading of the LED shots **counts as partial P0 evidence** (scope below). Control return is **not** proven.
- Next run `RUN-GAMEPLAY.cmd nativeonly cand5 zone`: **SAFE-IF**, i.e. GO after one dryrun of that exact combo shows the lines in CG1. Purpose PROBE P0+ only; not a proof5 run.

GO line (valid only after CG1 is met):

```
RUN-GAMEPLAY.cmd|B2B2BE248085E167FD1F2131F40871F380627F4D02599B28B33059FEE54C17EF|nativeonly cand5 zone
```

## What I checked (Z2)

- Shas of post, run log, sidecar.out and auto post equal the Overseer's; toypad-events.csv 8C38B18F equals the post's evidence table.
- ZG3: gameplay-run.ps1 691B70AD L213-217 `Sidecar-Args` adds `--led-shots`, and with `$Zone` `--zone --zone-delay 45` instead of the then-mark. The dryrun echo is L225-226 inside `if ($DryRun)`; the real launch L310-311 calls the same function. sidecar.out header: `zone ON (delay 45 s, gap 2 s, confirm 10 s); led shots on` and trigger `mark ''` (no then-mark); result `then=off`. Run log L3 ZONE line present; pinned MANIFEST C5181520; verify-bins 0 FAIL.
- My own extraction from toypad-events.csv (not the post):
  - T0 07:17:42.994; step 1 first command REMOVE gandalf confirm 07:18:28.466 (T0+45.47), LOAD wyldstyle pad 3 07:18:32.542 (T0+49.55), handoff 0.076 s; step 2 LOAD gandalf pad 2 07:18:36.883, handoff 0.065 s; step 3 LOAD batman pad 1 07:18:39.181, all-amber 07:18:39.287 (T0+56.29), handoff 0.106 s. No retry, skip or stop.
  - Red speed-18 from 07:18:56.461 to 07:20:40.808 on all 3 pads: 88 `FF 00 00` + 87 `00 00 00` rows per pad (the post's 175 counts both blink phases). done -> red-18 = 17.17 s (051159: ~17.5 s).
  - 7 shot rows (zone-t0, zone-cue-pad2, zone-cue-pad1, zone-done, alert1-plus05s/30s/60s); 1 alert row. 3 prompt rows, all before T0.
- Result line: `prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1 ctl=0 done/0 err ... zone=done zone-skips=0 alerts=1 shots=7`. load-confirms 9 / remove-confirms 6 = the 3 prompt answers + 6 zone commands.
- Route items 1-6: gate HIT try 1 at L55; 302/302, stop L310 t=880.27; same 10 non-gate TIMEOUTs; exits 0; keystrokes 0. The route is open-loop after L96, so the zone outcome could not add TIMEOUTs; FE path unchanged.
- G7/ZG6, re-hashed by me at 07:27: bin-native C5181520, bin-native5 787CD694, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9; live kit unchanged. No legodimensions process.

## PROBE P0 ruling

- Counts as P0 evidence (passive, from the automatic `--led-shots` rows): red-18 starts done + 17.2 s and was still blinking 104 s later at the route stop, and per the Overseer's viewing, the +60 s shot (`native-led-07-alert1-plus60s.jpg`) shows the in-level HUD (P1 Wyldstyle hearts, P2 Gandalf icon) while red-18 is on. So red-18 is not a cutscene-only or menu-only state.
- Limits: one frame, viewed by the Overseer (I did not view images, by rule). A visible HUD is not proof of player control: the route's walk inputs are open-loop and there is no input-response marker. The hand-check of control return and P1-P4 stay with the next manual session.
- Native4bp glare washes out the post-done scenes; that is a fair reason for the cand5 repeat.

## Why cand5+zone is clearable for P0+

- Code: in gameplay-run.ps1 691B70AD the two words are orthogonal. `$Zone` only changes the ZONE say line (L143) and the sidecar args (L217). `$Cand5` only changes the arm (L133), the fp (L139), the CAND5 line (L144) and the tag (L199). The word checks (L67-71) allow `nativeonly cand5 zone`.
- Both halves have now run for real, each with a clean result (064143 cand5, 070554 zone).
- It was not cleared for proof5 because a zone run changes the route outcome after T0 (P5). That reason doesn't apply to a P0+ run that claims no proof5 RESULT.
- What is missing: this exact combo has no dryrun, and ZG3-style checks rely on dryrun output as the reference. Hence CG1.

## Conditions (cand5 zone GO)

- CG1 First run `RUN-GAMEPLAY.cmd dryrun nativeonly cand5 zone` in its own slot (bin-native5 already equals source, so 0 bytes are copied; ~380 MB is re-hashed). It must show ALL of:
  - the ZONE line `--zone --zone-delay 45` AND the CAND5 line (native5pack-bin MANIFEST 787CD694F0B884D9, copy bin-native5, tag gp5-native, trace trace-native5-STAMP, `--expect-fp a349d5292f67b127`);
  - verify-bins PASS on native5pack-bin and on bin-native5 (787CD694, 0 FAIL);
  - SIDECAR line with `--tag gp5-native`, `--led-shots --zone --zone-delay 45` and no `--then-mark`;
  - prompt self-test A-F PASS; `dryrun-runs removed`; `DRY RUN ALL PASS (1 refusal note(s) ...)`, the note being the hidden desktop.
  If every item matches, the GO line above is valid without another round trip to me. Send me the dryrun log sha with the post. If anything differs: NO-GO, send it to me.
- CG2 Preflight: no legodimensions process; no GO.txt; no HOLD file; the waiter's last status line is END; live RUN-GAMEPLAY.cmd B2B2BE24, ps1 691B70AD, sidecar 1D9A6EB5; bin-native5 787CD694; bin-native C5181520.
- CG3 Exactly `nativeonly cand5 zone`, through the waiter on the interactive desktop. X1 hands off: 0 keystrokes, no external ctl writes; the only toypad actions are the sidecar's (3 prompt answers + zone commands). A kit refusal is a stop, not a retry.
- CG4 Real-run log: the ZONE and CAND5 lines as in CG1; pinned MANIFEST 787CD694; verify-bins PASS; `PASS native fingerprint: a349d5292f67b127`. The sidecar.out header must read `zone ON (delay 45 s ...); led shots on` and trigger `mark ''`, and the tag must be gp5-native. Any mismatch voids the run.
- CG5 Exclusive window until the waiter END.
- CG6 M3 post: items 1-6 as before; the Z3 items as in 070554 (T0, per-step commands and confirms on game_ts, handoffs, retry/skip/stop, full result line, red-18 first/last per pad and the done -> red-18 delta, shot rows with jpg names); a side-by-side with 070554 (native4bp zone) for T0, the three LOADs, done and red-18 start; and the G7 hashes. jpg names only; whoever views images is the Overseer's call.
- CG7 Claims allowed: functional only (P0+, second functional cand5 run). No timing claim, no proof5 RESULT, no promotion (N4). The proof5 baseline stays 064143. M16 may run proof5_post on this run for information only, in a separate `post-STAMP-p0info` dir, labelled informational. Its route line will differ after T0 by design, and its RESULT is not counted. A 0 missing-draw count on the post-done scenes would be new coverage beyond 064143 and is worth stating as such.
- CG8 After the run: bin-native C5181520, bin-native5 787CD694, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 unchanged. A crash, a gate miss, prompts other than 1/1, or a zone stop are reported as is. Any re-run needs a new GO.

## Findings

- SHOULD Z2-S1 (kit, next ps1 revision): echo the SIDECAR line in real runs too (M3's proposal), so the run log alone can be checked against its dryrun. Until then, the sidecar.out header is the accepted equivalent.
- NIT Z2-N1: the post's "175 rows/pad" for red-18 counts both blink phases (88 red + 87 off). State the split in future posts.
- NIT Z2-N2: the auto post still has no Z3 section; the zone and red-18 items were extracted by hand. A small read-only extractor would make Z3 repeatable.
