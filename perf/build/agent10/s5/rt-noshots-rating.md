# Rating: M2 RT-smoke `noshots` word + matched manual capture

M10 (Agent 10 successor), 2026-11-26 03:27. Static review. I ran nothing.

## Files

| file | sha256/16 | bytes | role |
|---|---|---|---|
| rt-smoke/delta-noshots/noshots.diff | 009030B0 | 6677 | the delta |
| delta-noshots/new/rt-smoke-run.ps1 | 02C6C88C89BE9124 | 27430 | live 4311865F (= orig/) |
| delta-noshots/new/RUN-RT-SMOKE.cmd | 34425077 | 4560 | live B7099FE4 (= orig/) |
| delta-noshots/new/rt-mark.ps1 | 80589B0D | 2131 | new, read-only timing helper (not run by the kit) |
| build/agent2/s5/manual_sbs.py | 7A881885 | 2970 | offline side-by-side maker |
| rt_smoke_post.py | 6034CA36 | - | unchanged |

## Base

rt-overlay-shotfix-rating 0BF83CF0. O1-O4 were closed at 03:14: the GO run B4FB5EB1 gave functional PASS and shots FAIL, and M2 stopped per O4.

## Verdict

**SAFE-IF N1-N6.**

## What I checked

- **The diff is complete.** `git diff --no-index --stat` orig→new:
  - ps1: 4+/3-, one changed code line plus doc and Say lines.
  - cmd: 2+/2-, the ps1 pin line plus the doc line.
  - The live files equal orig/ (B7099FE4 / 4311865F).
  - PS 5.1 ParseFile: new ps1 0 errors, rt-mark 0 errors.
  - The ps1 is LF; the cmd is CRLF (74 lines, 0 bare LF).
- **noshots logic.** `$ShotArms` is empty when 'noshots' is given, and the shot job only starts when `$ShotArms -contains $a.arm` (L352). So with noshots the kit puts nothing on screen: no PrintWindow, no overlay, no screen copy.
  - The post is unchanged. Its two screenshot gates FAIL by design, as stated.
  - All other gates (bins, P4 spatial, clean exit, error lines) are unchanged.
- **rt-mark.ps1** is read-only:
  - It only calls Get-Process and Start-Sleep, with no launch, close, focus or input.
  - It picks the newest legodimensions.exe whose image is under `<s5>\rt-smoke\runs\` and that is younger than 235 s, so it must be installed in build\agent2\s5\.
  - It exits 2 when there is no game or when the target time is more than 1 s past.
- **manual_sbs.py** is offline. It imports only argparse, hashlib, os, PIL and numpy, has no network or subprocess calls, and opens images read-only. ast OK (python -B).
- **The capture route.**
  - computer-cli `screenshot` and `zoom` are read-only (SKILL table: they save a PNG, with no focus or input).
  - No word whitelist exists in rt-smoke-run.ps1 (pre-existing), so a typo of `noshots` would silently run the kit's shot job (see N2).

## Conditions

- **N1 (install and dryrun):** only after EXPLORE2 ends (one kit at a time).
  - Install exactly ps1 02C6C88C, cmd 34425077 and rt-mark 80589B0D (to build\agent2\s5\rt-mark.ps1); the post stays 6034CA36.
  - Then pinsonly 14 OK, tamper ALL PASS, and `dryrun noshots` ALL PASS, whose log must contain `shots NONE (noshots: manual capture)`.
  - Send me the log sha and the installed shas.
- **N2 (GO form and word check):** GO only as `RUN-RT-SMOKE.cmd noshots arms=F3A,F3B`. Before the first screenshot, M2 confirms the real-run log shows `shots NONE (noshots: manual capture)`. If it doesn't, take no manual captures in that run.
- **N3 (replaces O2 for noshots runs only):**
  - During the F3 arms, only M2 uses computer-cli, and only `screenshot`, `zoom` and the read-only `windows`.
  - No focus, click, key, type, scroll, mouse_move or drag.
  - No other agent uses the screen.
  - If the game isn't the visible front window at a capture time, skip that capture and log it; don't activate it.
- **N4 (privacy and S3):**
  - Full-desktop screenshots never leave the machine.
  - Only the zoom crops of the game client area and the manual_sbs outputs may be posted to the user's webhook, images only. Before posting, M2 views each image and confirms it shows only game content (no other windows, notifications, toasts or text from other apps).
  - The Overseer confirms that the webhook is the user's sanctioned channel for these images. Everything else stays local, as S3 says.
- **N5 (usefulness stop, continues O4):**
  - Check the first capture pair (F3A 60 s) right away. If it is black or near-black, or not 1:1 physical pixels (check the PNG dimensions against the region; the screenshot long edge is ≤ 1366), stop capturing. The kit run may still finish as a functional smoke.
  - Report it and add no further capture variants without a rating.
- **N6 (carry-over):** R2-R5 and S3 (as amended by N4) carry over. Any post FAIL other than the two screenshot gates is a real failure.

## Findings

- **NIT:** rt-smoke-run.ps1 doesn't refuse unknown words (pre-existing). That's why N2 needs the log-line check.
- **NIT:** rt-mark isn't pinned by the kit. That's correct, since the kit never runs it; record its sha in the N1 message.
- **NIT:** if rt-mark is started for F3B while F3A's game is still under 235 s old, it picks F3A's game. It then fails loudly ("already past", exit 2) instead of mis-timing, so start it after F3A closes.
- **NIT:** the claim "1:1, 1366x800 physical" for the zoom region is unverified. A FSR1-vs-bilinear comparison needs 1:1 pixels, so check it on the first pair (N5).
- **NOTE:** the zero-diff alternative (kit shots plus manual shots between them) would need an O2 waiver. I agree with not preferring it.
