# natcmp kit delta rating (M16, after 4635DA35)

M10, 2026-11-25 19:50. Static review + my own scratch tamper tests + cmp_post selftest. No game, no runner, no dryrun run by me.

## Files

| file | sha256/16 | bytes | notes |
|---|---|---|---|
| build/agent16/RUN-NATCMP.cmd | 7FABD416041F32F0 | 4037 | CRLF 66/66 lines |
| build/agent16/natcmp/cmp-run.ps1 | 41A3F7BC5ADD3BB0 | 18993 | LF |
| build/agent16/natcmp/cmp_post.py | 52F53DB4DB3C4E11 | 27573 | LF |
| build/agent16/natcmp/matrix-natcmp.json | D0EE98BBF003354C | 1787 | |

All four match the Overseer's list.

Base: my rating natcmp-kit-rating.md 4635DA35 (RUN-NATCMP B5E90387, cmp-run B8963478, post EC900ABE, matrix 6261A9CE).

## Verdict

**SAFE-IF C1, C3, C4, C5.** B1 is CLOSED. S1, S2, N3 and N4 are fixed. C2 is met (my tests below + M16's 12/12).

## What I checked

**B1 (CRLF + fail-closed pins): CLOSED.**
- The .cmd is CRLF on every line. `:pin` increments PINOK on a match; the launch needs PINFAIL==0 **and** PINOK==19, else `goto :refused` (exit 3). 19 pins carry real hashes.
- My tamper tests on scratch copies in build/agent10/natchk/ (absolute WS paths, launch line replaced by `echo WOULD-LAUNCH`):

| case | rc | output |
|---|---|---|
| untouched | 0 | WOULD-LAUNCH |
| bad hash on one helper | 3 | 18/19 |
| missing file | 3 | 18/19 |
| `:pin` label renamed | 3 | 0/19 |
| converted to LF | 3 | "27/19 matched": the mis-seek is caught by the exact ==19 check |
| one pin line dropped | 3 | 18/19 |

- The run-matrix pin is in-process (cmp-run L39/L149): a mismatch is a refusal → exit 3 in a real run. It is re-checked before every arm (L206), which stops the session.

**cmp-run.ps1**
- Words: `vs ship|nat`, default ship60; both together, or `vs` alone → usage exit 2.
- `$bins` is filtered to the base arm + n4bp60. The ship60 MANIFEST pin 4A4A13ED…982D equals build/agent8/s5/window-s5.ps1 L28 and the live devfinal2-bin\MANIFEST.txt hash (I re-hashed it).
- S1 fixed: the L97 guard is M3's narrowed form (powershell/pwsh/cmd only; `-File "?…(window-s5|run-matrix).ps1` or `RUN-WINDOW-S5*.cmd`; own pid excluded). This is the pattern I tested against the live window at 18:40. Our own runner child isn't alive when Get-Refusals runs.
- N4 fixed: the timeout test adds GateWin before the next sample, so the gate never runs past 180 s.
- N3 fixed: after each arm, `$od` is re-resolved to the newest `^<leaf>(-\d+)?$` dir under the out root.
- Stop-Ours is unchanged in scope:
  - It runs only while an arm is active.
  - It kills a legodimensions.exe only if its ExecutablePath starts with the resolved `natcmp\matrix\<stamp>\`. That root is fresh per invocation. A hard-linked image elsewhere has a different path, so another agent's game can't match.
  - It kills a powershell only if its PPID is this process and its command line has run-matrix.ps1.
- Post args now carry `--base $Base`. Writes are post\natcmp-*.txt, post\SHA256SUMS-*.txt, LATEST.txt, logs\. The dryrun's dryrun-matrix delete is reparse-checked (refuses and counts as a failure if any reparse point is present).
- Everything else matches what I rated in 4635DA35: preconditions, per-arm verify-bins + Get-Refusals, and the gate after verify-bins.

**matrix-natcmp.json**
- The run settings equal matrix-s5-baseline.json key by key (warmup/measure/min_window/boot/close/cooldown/sys_csv/input_script/gpu_log/3D thresholds).
- The ship60/nat60/n4bp60 arms have the same bin, frames and cap as the baseline. reference = ship60.
- Only cold_run (false), repeats (1) and order differ. That is as documented.

**cmp_post.py**
- No subprocess. Writes go only to `--out` (makedirs on its parent) and to a mkdtemp tree in the selftest, which is rmtree'd in finally.
- `--base` choices are ship60|nat60. A bad label, e.g. `s1-ship99`, → exit 2, and so does `--base ship`. I tested both.
- S2 fixed: MIN_PAIRS = 2. With one valid pair the result is `INCONCLUSIVE (only 1 valid pair; indicative: …)`.
- Pairs are (s1,s2), (s3,s4)… and must be exactly one base + one n4bp60. Mixed base arms are flagged and only base pairs count. `--base nat60` on ship runs → 0 valid.
- Clean-second rule: nongame < 4.0 cores only. CLEAN_USES_EFF = False, and the rationale is in L41-43: the CPU clock tracks the arm's own GPU power under shared cooling. The rule is printed in the report header via clean_rule(). CONFOUNDED (> 25 % unclean, or no sys.csv) uses only nongame. eff MHz is still a per-run column.
- The pre-arm gate in cmp-run (20 s mean < 2.0, max < 4.0) is unchanged and stricter than the per-second flag.
- My run: `python -B cmp_post.py --selftest` → SELFTEST PASS, 32 checks, 0 failed, rc 0 (cases G-K cover S2, ship base, mixed base, wrong base).

## Conditions

- **C1:** after rows (the Overseer's order) and outside the user's pause. One kit at a time. On the interactive, unlocked desktop.
- **C2:** MET. See the tamper table and M16's 12/12.
- **C3:** OPEN. A dryrun with ALL PASS: every runner -PlanOnly exits 0, the gate sample has 5 values and the cmp_post selftest passes. natcmp\logs\ doesn't exist yet, so no dryrun has been run on these hashes. Send me the log sha.
- **C4:** if any of the 4 files changes before the run, re-hash and send me the shas for a match. Any change to cmp-run.ps1 also changes the .cmd pin.
- **C5:** the read-out quotes "valid pairs k/n" and the base arm. If the verdict is directional, also quote each pair's eff MHz: the clock is no longer a clean-second criterion, so a large clock gap between the two runs of a pair has to be eyeballed.

## Findings

- **N1 (NIT, carried):** abort kills are forced (Stop-Process -Force). Abort path only.
- **N2 (NIT, carried):** verify-bins re-hashes ~380 MB before each arm, ahead of the gate. That's harmless.
- **N5 (NIT, new):** ship60 frames come from perf.csv (xenos) and n4bp60 frames from native-frames.csv. This is the same split that score3d used in the window, so the fps comparison inherits score3d's cross-renderer equivalence. The recomputed-fps check (> 1 % differs from score3d → note) applies to both.
