# Rating: M2 RT-smoke screenshot fix (shotfix)

Who/when: M10, 2026-11-26 ~01:53 local. Static review plus PS 5.1 ParseFile and py_compile (no kit run).

## Files (sha256/16, bytes) - WS\build\agent2\s5\

| file | sha256/16 | bytes |
|---|---|---|
| rt-smoke/delta-shotfix/shotfix.diff | C8B5BA230E8695BA | 12122 |
| RUN-RT-SMOKE.cmd | A8BA4BF69F7EDE2E | 4512 (CRLF 75/75, 14 pins) |
| rt-smoke-run.ps1 | 9CEBC45BA5A925C4 | 24305 |
| rt_smoke_post.py | 6034CA362A1FDDFA | 22829 |
| delta-shotfix/orig/* | 0F33351C / 630D1F00 / 0419882C | = the rated 5D991653 set |

Base: rt-smoke-kit-rating.md 5D991653 (R1-R5; R1 closed by dryrun ABE4A6AB). Run 01:32-01:45: PASS T2/F3A/F3B, but all 8 F3 shots were black (PrintWindow vs the flip-model swapchain).

## Verdict: SAFE-IF (S1-S3)

## What I checked

- Completeness: `git diff --no-index --stat` orig vs new gives ps1 +57/-1, post +42/-9, cmd +2/-2, matching shotfix.diff. The cmd change is only the two pin hashes (ps1, post); still 14 pins with PINOK==14 fail-closed.
- PS 5.1 ParseFile on rt-smoke-run.ps1 9CEBC45B: 0 errors (the job scriptblock and here-string included). py_compile on the post: rc 0.
- ps1 delta (shot job only):
  - LdKitCap (Add-Type in the job process): NonBlack reads the PNG and samples 96x96 below the title bar. ScreenCopy uses only GetForegroundWindow, GetWindowRect and Graphics.CopyFromScreen, then saves a PNG.
  - It does no SetForegroundWindow, no input and no window messages, so it's read-only towards the desktop.
  - Fallback only when the PrintWindow share is < 5% and the game's own MainWindowHandle (pid found by the existing under-runsRoot/StartTime filter) is the foreground window. Output goes to `<run>\kit-shots\shot-NNNs-screen.png` plus a shots.txt line.
  - DPI: the display is at 144 DPI (150%). winhelper's static ctor LdHarness() sets per-monitor-v2 DPI awareness, and it runs before ScreenCopy because [LdHarness]::Shot is called first in every iteration. So GetWindowRect and CopyFromScreen both use physical pixels and the rect is not offset.
  - Errors: a throwing NonBlack (bad PNG) can at most end the shot job early. Fewer shots means a post FAIL, which is the safe direction.
- post delta:
  - The shot gate is now by pixels (`client_nonblack`, R+G+B > 24 below min(40, h/4) rows, >= 2%) per time, PrintWindow first and the screen copy second. All 4 times must have a usable pick. The shots.txt labels are no longer trusted.
  - side_by_side uses the same pick. Still writes only under rt-smoke/post.
  - A black PrintWindow + fps counter measures 0.4% (M2), well below 2%. A dark real frame (6.6%) passes.
- Pins, refusals, lock-equivalents, hold job, Stop-Ours and arms: unchanged (outside the hunks).

## Conditions

- S1: R2-R5 carry over. Dryrun ALL PASS on cmd A8BA4BF6 before the GO `arms=F3A,F3B`; send me the log sha.
- S2: during F3 arms, leave the game window in front and uncovered: no computer-cli screenshots/clicks or other windows on top. The screen copy captures whatever is on screen inside the game's window rect at that instant.
- S3: the shot PNGs stay local in the run dir (they can contain on-screen content). Only side-by-sides of game frames are shown to the user.

## Findings

- NIT N1: TOCTOU between the GetForegroundWindow check and CopyFromScreen (microseconds). A topmost window or toast over the game rect would also be captured, and could make a black frame pass the 2% gate. Hence S2; the side-by-sides are reviewed by eye anyway (R5).
- NIT N2: the 2% threshold is calibrated on two samples. A very dark scene at a shot time could false-FAIL (safe).
- NIT N3: if the game isn't in front at a shot time (e.g. the user clicks elsewhere), that time has no usable shot and the arm FAILs on shots only (safe; the frames/FSR gates are independent).
- NIT N4: Add-Type compiles C# in each shot job (csc, temp files, ~1-2 s CPU at job start, before the first shot at 60 s). Fine for a functional-only kit (R3).
