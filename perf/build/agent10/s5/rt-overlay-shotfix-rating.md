# Rating: M2 RT-smoke overlay shotfix delta (screen copy via a compose overlay)

Who/when: M10, 2026-11-26 ~02:52 local. Static review plus PS 5.1 ParseFile (no kit run).

## Files (sha256/16, bytes) - WS\build\agent2\s5\

| file | sha256/16 | bytes |
|---|---|---|
| rt-smoke/delta-overlay/overlay.diff | 754987F9FD248479 | 46 lines |
| RUN-RT-SMOKE.cmd | B7099FE4267AECA7 | 4512 (CRLF 74/74, 14 pins) |
| rt-smoke-run.ps1 | 4311865FD6ECC515 | 27158 (ParseFile 0 errors) |
| rt_smoke_post.py | 6034CA362A1FDDFA | unchanged |
| delta-overlay/orig/ | 9CEBC45B (ps1), A8BA4BF6 (cmd) | = the rated shotfix set (425A6D25) |

Base: rt-shotfix-rating.md 425A6D25 (S1-S3) on top of rt-smoke-kit-rating.md 5D991653 (R1-R5).

## Verdict: SAFE-IF (O1-O4)

## What I checked

- Completeness: `git diff --no-index --stat` orig vs new gives ps1 +40/-4 and cmd +1/-1, matching overlay.diff. The cmd changes only the ps1 pin line (14 pins, PINOK==14 fail-closed). The ps1 changes only the LdKitCap class and the comment above $shotJob.
- PS 5.1 ParseFile on 4311865F: 0 errors.
- ScreenCopy flow:
  1. h must be the foreground window (unchanged).
  2. CreateWindowExW("STATIC", "ld-kit-compose", WS_POPUP) with WS_EX_LAYERED|TRANSPARENT|TOPMOST|NOACTIVATE|TOOLWINDOW over the game's window rect.
  3. Alpha 1/255, SW_SHOWNOACTIVATE.
  4. Pump the job thread's own messages for 500 ms.
  5. Foreground re-check (else no copy).
  6. CopyFromScreen.
  7. Foreground re-check (else no PNG is saved).
  8. DestroyWindow in finally.
- Effect on the game and the user:
  - NOACTIVATE + SW_SHOWNOACTIVATE: the game keeps activation and keyboard focus.
  - TRANSPARENT + LAYERED: mouse input passes through.
  - TOOLWINDOW: no taskbar or alt-tab entry.
  - The window is created and destroyed on the same thread (DestroyWindow is valid there) and dies with the job process if the job is killed, so it can't be left behind.
  - The game sees only a change from independent flip to DWM composition for ~0.5 s per fallback shot (the same as a toast or computer-cli's border). That can cause a frame-time blip, which is irrelevant for a functional-only kit (R3).
- Gate integrity: the overlay can't fake a PASS. At alpha 1/255 the STATIC background adds about 1 per channel (R+G+B ~ 3), far below the post's R+G+B > 24 pixel test. A black game frame still measures ~0% and fails the 2% gate. The post, pick_shot, shot times and the 5% fallback trigger are unchanged.
- M2 tests: shotoverlay test PASS (821E1074), on the hidden desktop with the foreground checks stubbed and CopyFromScreen/PNG skipped. So the capture itself is unproven until the first real run. A failure there gives "no usable shot" -> a shots FAIL, which is safe.
- Evidence files as stated: tamper 21/21 (5F91D5BE), guard regex (96264F9A), shotcap (B89F8D51), shotgate 6/6 (85E4EB42), pinsonly (DD22026C).

## Conditions

- O1: dryrun ALL PASS on cmd B7099FE4 before the GO `arms=F3A,F3B` (~9 min); send me the log sha. The GO comes only after the RUN-MANUAL session has fully ended (the kit's game-running refusal enforces this too).
- O2 (replaces S2): for ~0.5 s per fallback screen copy, an invisible, click-through, no-activate topmost overlay covers the game window. The game must be foreground before and after, or the shot is discarded and logged. During the F3 arms: no computer-cli screenshots, clicks or keys, and no other window activated. A foreground change only loses shots (safe), but keep the arms undisturbed.
- O3: S3 and R2-R5 carry over (PNGs stay local in the run dir; interactive desktop; one kit at a time; functional only; re-pin on any change; the FSR overlay toggle stays a manual user check).
- O4: if the first real F3 run still gives no usable shots, stop and report. No further capture variants (e.g. focus changes, SetForegroundWindow, input) without a new rating.

## Findings

- NIT N1: SettleMs 500 is a guess ("~30 frames"). If DWM needs longer to leave independent flip, the copy is still black -> a false FAIL (safe). It's public static, so tune it via a re-rated delta, not ad hoc.
- NIT N2: the return values of SetLayeredWindowAttributes and ShowWindow aren't checked. If they fail, the copy is simply black (safe).
- NIT N3: the overlay covers the whole window rect including the title bar. That's harmless because it's click-through, but a user's click during the 0.5 s still reaches the game window, as intended.
