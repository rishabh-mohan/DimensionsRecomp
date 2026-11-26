# nops-smoke kit final delta + Z2/V1 rating (M2, after 3263F064 and 294BD7A7)

M10, 2026-11-25 19:52. This is a static review. I re-hashed every pin and the bin, and tested the guard regex on strings. I ran none of M2's scripts, no game and no dryrun.

## Files

| file | sha256/16 | bytes | notes |
|---|---|---|---|
| build/agent2/s5/RUN-NOPS-SMOKE.cmd | AF57C90E5773CAF2 | 3975 | CRLF 63/63 |
| build/agent2/s5/nops-smoke-run.ps1 | 1D93442E3BD0BCD4 | 21500 | LF |
| build/agent2/s5/nops_smoke_post.py | 54BA5CF9D85418DF | 21304 | LF |
| build/agent2/s5/nops_smoke_post-delta.diff | A130DA444A81FD41 | 4082 | vs CA522270 |
| build/agent2/s5/KIT-DELTA.md | 9F2808E60108BAFC | 3797 | |
| build/agent2/s5/pins-test/tamper-test.txt | 0697FDD52D4DB856 | 5766 | 17/17 PASS |
| build/agent2/s5/nops-bin/BIN-PINS.md | 0BA90CC99F5B6CFE | 2601 | |
| build/agent2/s5/nops-bin/build-s5nops.py | FDC959418D82FEBE | 20721 | not re-reviewed (dryrun-only fixes per M2) |
| build/agent2/s5/nops-smoke/synth/synth_post.py | AE08FB825E067554 | 3447 | not run by the kit |

The bin, build/agent2/s5/devs5nops-bin, which I re-hashed:
- MANIFEST 8A8B2E776D896F12 = the ps1 `$pin` (L47) = BIN-PINS;
- exe 6C8E281156CCE828 = devfinal2;
- rexruntime 641BD22519921ACD = devfinal2;
- rexgpu-xenos 55BE4D19142A0EE5 (devfinal2 has 9A7CC3F4: the only file that differs).

Base: nops-smoke-kit-rating.md 3263F064 (K1-K7, S1-S4), zpd-log-v2-rating.md 294BD7A7 (Z1-Z5, V1).

## Verdict

**SAFE-IF K3-K7, Z3-Z5 + D1-D2.**
- Closed: K1, K2, Z1, Z2 and V1.
- S1-S4 are applied.
- The guard catches all 3 real window launch forms.

## What I checked

**K1 (bin staged): CLOSED.**
- The MANIFEST pin is set (L47) and matches the bin.
- BIN-PINS says verify-bins passed at stage.
- The bin uses the two rated TUs: stk 9B92AAF9 (pipeline_cache) and ov 6DE509E3 (command_processor). The zpd-log TU is stacked, so Z1-Z5 apply and `nozpd` isn't needed.

**Z1/V1: CLOSED.**
- zpd-log/check.txt: RESULT PASS on diff 5CAD04BB and ov 6DE509E3 (SDK HEAD a7e79c0, base and final2 overlay == the blob 00EA93D3, add-only, git apply clean).
- zpd-log/check-compile.txt: fsyntax + compile exit 0 with the final2 gpu command on ov 6DE509E3. obj 75BA5D18, needles present, RESULT PASS.
- nops-async/check-compile.txt: stacked 9B92AAF9 → obj CB8A004B, RESULT PASS.
- Warnings are 1 pessimizing-move + 7 unused-parameter + 1 unused-lambda-capture. M2 says they are identical to BASE. I saw the unused-parameter lines; I didn't diff them against BASE.

**Z2: CLOSED for ov 6DE509E3.** New bin dir with its own MANIFEST, from the final2 gpu leg + the two TUs. BASE recompiles == final2 objs except TimeDateStamp. The exe and rexruntime equal devfinal2 (re-hashed). No pinned or shipped bin was touched: the devfinal2 MANIFEST is still 4A4A13ED.

**K2 (re-pin): CLOSED.**
- The .cmd is CRLF and pins 13 files. I re-hashed all 13 against the .cmd lines: 13/13 match.
- The helper pins equal the values rated elsewhere: run-game C2533FDF, guard 7A71E720, winhelper 37619E3D, nvml 9F6E6E3B, runstats AE6C8B0C (= M3's GPPIN_20), vpadhost 5D929041, toml B763DABB, attract-long 4D35FAF4, xinput 309DF316, verify-bins 80FF4C5F, check-defaults D9936C56.
- M2's tamper log has 17/17 PASS: each of the 13 files tampered → 3, a deleted file → 3, the dryrun word → 3, the clean copy → 0, a stub ps1 → its rc passes through.

**S1 (refusals): APPLIED.**
- Get-Refusals runs at the start and again before every arm. It covers WINDOW-HOLD, WINDOW-GO, the day launcher, a running game, Get-ActiveRunners, the hidden desktop and the window kits.
- The window-kit check only looks at powershell/pwsh/cmd/python/py processes, and needs `[\\/]` followed by `window-s5.ps1`, `RUN-WINDOW-S5*.cmd` or `run-matrix*.(ps1|cmd|py)` on the command line.
- I ran the regex against the 3 real launch forms. All three match:
  - cmd `/c ""…\RUN-WINDOW-S5.cmd" "`;
  - powershell `-File "…\window-s5.ps1"`;
  - powershell `-File …\run-matrix.ps1` (unquoted).
- A name-only grep (`-Pattern 'window-s5|run-matrix|RUN-WINDOW-S5'`) does not match. A grep or read that passes a **full path** to window-s5.ps1 does match. See D1.

**S2 (shot job): APPLIED.** It takes only a legodimensions process that has StartTime >= t0-2 s **and** Path under `<runsRoot>\`. kit-shots go next to that image, so they stay inside our run dir. The job is read-only (Shot only).

**S3 (cleanup + hold): APPLIED.**
- The arm loop is in try/catch/finally Stop-Ours. Stop-Ours:
  - stops our shot and hold jobs;
  - while an arm is active, force-stops only a legodimensions.exe whose ExecutablePath is under the runs root;
  - stops only a child powershell (PPID = self) that is running run-game.ps1.
- The per-arm hold job polls WINDOW-HOLD every 2 s. When the file appears, it sends CloseMainWindow to our game (path under the runs root only), and forces a stop after 15 s. Any hold output stops the kit before the next arm.
- The runs root (nops-smoke\runs) is not per-invocation, but no other agent runs a game there, and a second instance refuses on "a game is running".

**S4/K6 (bin re-check): APPLIED.** Check-Bin (verify-bins + MANIFEST == pin) runs after every arm, and a FAIL stops the kit with "results invalid". The last arm's check is the after-session check. It is skipped when an arm is stopped by a hold or an error. See D2.

**nops_smoke_post.py delta (A130DA44, +23/-9): Z4/Z5 applied.**
- Z4: the "shutdown line once" check is now a gate (`g`).
- Z5:
  - no `first` line or zpd == 0 → "proves nothing about S1";
  - no_ps > 0 → "S1 CONFIRMED";
  - "valid 0" only with begun > 0, resolved > 0, the first disable at or after half the ZPDs (or never), and a host fraction >= 0.5;
  - anything else → "0 NOT valid";
  - PS-only drops are tagged as HEAD behaviour.
- `zpd_no_host` is a real key: ZPD_KEYS L39 and the diff's log format.
- With `--nozpd`, zpd_report isn't called (arm_gates zpd=False), so the Z4 gate doesn't misfire.
- Writes: `--out`, plus joined-*.log under nops-smoke\post. The only subprocess is check-defaults.py (pinned), run via sys.executable. This is unchanged from CA522270 apart from the delta.

## Conditions

- **K3:** dryrun after the user's pause, on the Overseer's GO. It must be ALL PASS: every run-game -DryRun exits 0, the shot-job and hold-watch self-tests pass, the post selftest passes with all 3 needles, and the dryrun-runs delete passes its reparse check. Send me the log sha. The real run comes after that, with no window kit and no WINDOW-GO.
- **K4:** one kit at a time, and no other launcher during the session.
- **K5 (relaxed):** a hold now takes effect within about 2 s + 15 s. An abort is cleaned up by the finally block. Closing the console window still skips the finally, so don't do that mid-arm.
- **K7 / Z3:** this is a diagnostic bin, for smoke and functional use only. Never time it against devfinal2 or the native bins.
- **Z4/Z5:** read-out per the post verdict strings. An arm with "no ZPD on this route" proves nothing about S1.
- **D1:** during the session, no agent runs a command line that holds a full path to window-s5.ps1, run-matrix*.ps1 or RUN-WINDOW-S5*.cmd. The guard matches path + name, not `-File`, so such a command would refuse the next arm. That is fail-safe, but it loses the remaining arms. Optional: narrow it to M3's `-File` form.
- **D2:** if the kit stops on a hold or an error, run verify-bins on devs5nops-bin by hand (K6), because Check-Bin is skipped on those paths.
- If any kit file changes, re-run mkpins and send me the new shas.

## Findings

- **N1 (NIT):** the .cmd counts mismatches only (BAD). A missing `:pin` label would leave BAD at 0. The file is CRLF, so cmd can't mis-seek, and the waiter pins the .cmd itself, so this is not exploitable. The natcmp-style `PINOK==13` would make it fail-closed.
- **N2 (NIT):** BIN-PINS lists the ON objects (96ABB19D, F62E839C) from the leg build. These differ from the check-compile objs (CB8A004B, 75BA5D18) because the build paths and flags differ. That's expected; quote the leg objs as the bin's.
- **N3 (NIT):** the bin was built 19:46-19:47 at idle priority, which overlaps M3's explore slot. Explore is functional, not timed, so this doesn't matter here. Avoid it for any timed run.
