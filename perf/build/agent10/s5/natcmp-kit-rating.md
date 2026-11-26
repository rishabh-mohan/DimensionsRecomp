# M16 natcmp kit: fresh rating (pre-read, before M16's pin fill)

M10, 2026-11-25 19:35. I read every file in the kit. I ran one test, on a scratch copy of the .cmd in build/agent10 (see B1). I ran none of M16's scripts.

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent16/RUN-NATCMP.cmd | B5E903879BCD88B7 | 3527 (LF only: 0 CR, 58 LF) |
| build/agent16/natcmp/cmp-run.ps1 | B8963478053A3C61 | 17357 |
| build/agent16/natcmp/cmp_post.py | EC900ABE1A8783DD | 19902 |
| build/agent16/natcmp/matrix-natcmp.json | 6261A9CE35157C22 | 1532 |

Base:
- M8's rated S5 runner (PINS-S5 BE96CED7): run-matrix 8D647918, run-timing 72B8C69C.
- harness guard 7A71E720, winhelper 37619E3D.
- Bin MANIFEST pins: nat60 4E5E2620, n4bp60 C5181520. These are the same as window-s5.ps1 L29-30.

## Verdict

**UNSAFE as it stands, because of B1.** With B1 fixed it is SAFE-IF C1-C5. The design is sound: the kills are confined, the writes are confined, and it uses the same settings as the window.

## What I checked

**Pin coverage (.cmd L14-32):**
- It pins 3 kit files, still PENDING, so they fail safe.
- It pins 14 files from the S5 runner set:
  - 10 S5 files: run-timing, score3d, common, timing-env, winhelper.cs, frame_summary, sys_summary, sys-csv, LdSys, thread-cpu;
  - 4 PINS-S5 harness/helper files: attract-long, nvml, xinput1_4.dll, verify-bins.
- It pins harness guard 7A71E720 and harness winhelper 37619E3D.
- Every value equals its line in PINS-S5.txt.
- Not pinned by the .cmd, which is correct:
  - window-s5.ps1 and matrix-s5-baseline.json, which aren't used;
  - run-matrix.ps1, which cmp-run pins in process with Get-FileHash before every arm (`$rmPin` 8D647918, L37/L66-71/L197). That keeps the name off a certutil command line (D1).

**Runner use:**
- Each arm is `run-matrix -Matrix matrix-natcmp.json -Only <arm> -Repeats 1 -NoCold -NoPrompt -OutDir natcmp\matrix\<stamp>\NN-label`. All of these parameters exist in run-matrix 8D647918 (L38-48).
- run-matrix calls run-timing in process (L26), so the runner is one child powershell.

**Matrix:**
- Compared with matrix-s5-baseline.json, only these keys differ: cold_run (false), cold_* keys (absent), order (fixed), repeats (1) and reference (nat60).
- The nat60 and n4bp60 arms have the same bin, frames and cap as the window's arms.

**Kills (Stop-Ours L177-191, finally L223, only while `$armActive`):**
- The game: a legodimensions.exe whose ExecutablePath starts with `<resolved outRoot>\`. A game started through a hard link reports the path it was started from, so another agent's game can't match.
- The runner: a powershell with PPID == $PID and `run-matrix.ps1` on its command line.
- Nothing else is killed.

**Writes:**
- Under natcmp\: logs\, post\, matrix\<stamp>\ (run-matrix writes only under -OutDir, L506-512), LATEST.txt and dryrun-matrix\. dryrun-matrix\ is deleted only after a reparse-point check (L166-170).
- The bins are read-only: the runner hard-links them, and the PSO saves are temp+rename (a8e8dc8).
- cmp_post.py writes only --out. Its selftest uses its own mkdtemp dir and deletes only that. It starts no subprocesses.

**Guards (Get-Refusals L72-93, re-checked before every arm and again after the gate):**
- HOLD/GO files, the day launcher, any running game, Get-ActiveRunners, the window command-line check (L88) and a hidden desktop.

**Exit handling:**
- An arm that ends with exit 1 is recorded and the session goes on.
- Exit 2, or any other code, stops the session.
- A refusal stops the session.

**Post logic:**
- Primes (`prime-*`) are unscored.
- Pair k = s(2k-1) + s(2k). A pair is valid only if both runs are OK, neither is CONFOUNDED (more than 25 % unclean seconds) and neither is GATE-TIMEOUT.

## B1 test (scratch, build/agent10/s5/scratch-natcmp/)

I copied RUN-NATCMP.cmd byte for byte. The only change: the launch line (L39) became `echo WOULD-RUN-CMP-RUN`, padded to the same length, so every byte offset is kept. From the scratch dir every pinned path is missing.

- **LF copy (as shipped):**
  - The pins were checked out of order: the first line printed was winhelper.cs, and cmp-run.ps1 was never reported.
  - The REFUSED block ran 3 times ("1", "7", then "20 pinned files"). Each `exit /b 3` ran inside a `call :pin` frame, so it returned only from the call and the script carried on.
  - It ended at rc 3 here only by luck of where the labels fall.
- **CRLF copy:** it printed 19 PIN MISSING lines in order, one REFUSED, and exited 3.

cmd's label search and its resume position after `call` are known to break on LF-only batch files. Here that bug means a pin mismatch might never be checked, or that the script might fall through to the launch line. That breaks the kit's main safety promise: the waiter pins only this .cmd.

## Conditions (after B1)

- **C1:** after the window and freeze. One kit at a time. On the interactive, unlocked desktop.
- **C2:** pins filled in. Tamper tests on the CRLF .cmd: untouched → OK; +1 byte on cmp-run, on a helper and on run-matrix (in-process pin) → 3; missing file → 3.
- **C3:** dryrun is ALL PASS: every runner -PlanOnly exits 0, the gate sample has 5 values and the cmp_post selftest passes.
- **C4:** re-hash the final 4 kit files and send them to me for a hash match.
- **C5:** the read-out quotes "valid pairs k/n". See S2.

## Findings

- **B1 (BLOCKER): RUN-NATCMP.cmd is LF-only.** See the test above.
  - Fix: save it with CRLF; RUN-PSO-ROWS, RUN-WINDOW-S5 and RUN-NOPS-SMOKE are all CRLF.
  - Make the pin check fail closed: `:pin` increments PINOK on a match, and the launch requires `PINOK==19` as well as `PINFAIL==0`.
  - Re-run C2 on the CRLF file.
- **S1 (SHOULD): the L88 command-line guard is broad (D1).** It matches `window-s5\.ps1|RUN-WINDOW-S5|run-matrix` in any process. Here it is re-checked before every arm, and a refusal stops the session, so an agent shell that greps those names mid-session loses the remaining arms.
  - Narrow it the way M3 did: process name powershell/pwsh/cmd, and the command line matches `-File\s+"?[^"]*(window-s5|run-matrix)\.ps1` or `RUN-WINDOW-S5[^\s"]*\.cmd`.
  - At 18:40 I tested that pattern against the live window: it matched all 3 real processes (the cmd, window-s5, run-matrix) and not a grep shell.
  - Our own runner child isn't alive when Get-Refusals runs.
- **S2 (SHOULD): one valid pair is enough for a directional verdict.** cmp_post gives SLOWER/FASTER when *all* valid pairs exceed ±5 %, and that includes a single valid pair. In the short form (2 pairs), one confounded pair leaves an n=1 verdict.
  - Require at least 2 valid pairs for SLOWER/FASTER. Otherwise report INDICATIVE or INCONCLUSIVE.
- **N1 (NIT): abort kills are forced.** On abort, Stop-Ours uses Stop-Process -Force on the game and on the runner, so run-timing's finally doesn't run for that arm. The game kill by path covers it, and the sys sampler stops when the game exits. This happens on abort only.
- **N2 (NIT): verify-bins before each arm.** It re-hashes about 380 MB before every arm, just before the gate. That's harmless, because the gate samples afterwards, but it adds about 10-20 s per arm.
- **N3 (NIT): a run-matrix OutDir collision would hide a run.** If an OutDir already exists, run-matrix adds a `-N` suffix, and cmp-run's `$od` lookup (L211/L217) would then miss the run. The stamp dirs are fresh, so this can't happen today.
- **N4 (NIT): the gate timeout runs a little long.** It is checked after each 20 s sample, so it lasts up to about 200 s, not 180 s.
