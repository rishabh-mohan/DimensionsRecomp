# Launcher review: bench/agent5/launch/ (Agent 11, task #10)

Status: **FORMAL VERDICT (22:31): SAFE** on run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B and README 0058C8F6 (see the Formal verdict and Final sections below). After it: Agent 10 rated the same 3 files SAFE (22:33, b2r row 41/§40); the RUN-NIGHT.cmd STOP smoke test ran at 22:34 (exit 2, as expected); Agent 1 approved the 3 files for the 23:30 freeze (22:36, SESSION2 L3054-3070); and the W9/W5b/W4c GO lines checked OK at 22:45 ([GO-CHECK.md](GO-CHECK.md)). Before it: pre-read 20:58 (updated 21:03); interims v3 at 21:15, CD64BC93 and 3EFC5312 at 21:25, the 21:25/21:29 MUSTs and README 581A03DB at 21:35, B0902106 at 21:55. Hard deadline 23:00 (Agent 1 at 21:01).
Agent 1's classification (21:01): **must-fix** F1, F3 and README L151; **should-fix** F5; **optional** F4 and F6, and no WINDOW-CANCEL.
Reviewer rules: read-only on bench/agent5/launch/. Nothing launched, built or changed outside build/agent11/.

## Files

| Version | File | sha256 | Notes |
|---|---|---|---|
| v1 (20:26) | run-night.ps1 | 00BFECD70584FC8EE6D292B6884F70CA17854B7A16DC1DA397C729E44738AD0E | 49,599 B, 678 LF lines. Read in full. Copy: [v1-00BFECD7](v1-00BFECD7/) |
| v1 | RUN-NIGHT.cmd | FCB0441883AC468D702CE32C7D3BAFE9753EA130ADDE5BC5FA3EEE4C5D67BD86 | 979 B, LF only |
| v1 | README.md | 01C4D90F89DAAF9B0DBB5404FD7B440F410BA0226A0935C996A564BECD3164AB | 11,733 B (20:15:48) |
| v2 (20:50:26) | run-night.ps1 | 924321AE3A2C6686CBA446284F3B8F7FBB9178858DC2840A7320B382D965BDFC | 57,811 B, 788 LF lines, ASCII, no BOM, PS 5.1 ParseFile 0 errors. Copy: [v2-924321AE](v2-924321AE/). Diff: [diff-v1-v2.txt](diff-v1-v2.txt) (+149/-39) |
| v2 (20:51:01) | RUN-NIGHT.cmd | F7190AB228CF0EF90980103B04F079AFC5CE23BC92E3390A3A539D2C25CD5EAF | 1,012 B, CRLF (18 CR / 18 LF) |
| v3 (21:01:12) | run-night.ps1 | 163D76596E575D8D4684417869AE8C8D67E92CE7E38D17BD1172014BBD0DAF69 | 63,759 B, 846 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy: [v3-163D7659](v3-163D7659/). Diff: [diff-v2-v3.txt](diff-v2-v3.txt) (+81/-23). Interim read below |
| p-2114 (21:13:38) | run-night.ps1 | CD64BC93017083B1190CA6AB858E60A1956A1B2DE02588D4EAA20031A1AD439C | 71,763 B, 944 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2114-CD64BC93](p-2114-CD64BC93/). Diff v3→CD64: +138/-41, read in full. Interim read below |
| p-2119 (21:15:40) | run-night.ps1 | 3EFC5312D0982E77D0F92D154D54EB063D9495A63812432113DEE65859630E5C | 72,276 B, 948 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2119-3EFC5312](p-2119-3EFC5312/). Diff CD64→3EFC: +5/-1 (F1 only). Interim read below |
| (20:53:42) | README.md | 39ECF5C21234B500… | 16,507 B; only searched so far (L117, L163, L170, L202); full read in the formal pass |
| (21:28:05) | README.md | 581A03DB66D34A276684F1AEC242FD0B14290C58748302C706DC9CEBF4F81D13 | 21,508 B, 263 LF lines, no CR. Copy, diff and grep: [r-2128-581A03DB](r-2128-581A03DB/). Interim read below; full read in the formal pass |
| p-2147 (21:42:43) | run-night.ps1 | B0902106C4D935810C5747951095053E117165BE36CF8FE1F32B0C0337E8DB33 | 77,221 B, 1010 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2147-B0902106](p-2147-B0902106/). Diff 3EFC→B090: +89/-27, read in full. Interim read below |
| p-2214 (22:11:21) | run-night.ps1 | 16B90FA8654FAC088FE5A1248DE1754918AACC7667A2126AD14723BFBF939B31 | **Final.** 77,594 B, 1017 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2214-16B90FA8](p-2214-16B90FA8/). Diff B090→16B9: +8/-1, read in full |
| (21:51:46) | RUN-NIGHT.cmd | D7A0362BE90C12B4F027116B9A5146D1F4C8D109110F885EE8CF62E6769DE6D5 | **Final.** 1,197 B, CRLF (19 CR / 19 LF), no bare LF, ASCII. Diff against F7190AB2: [p-2214-16B90FA8/diff-cmd.txt](p-2214-16B90FA8/diff-cmd.txt) |
| (22:12:38) | README.md | 0058C8F61EEAA9F2529145B034433E2FB67344012D114E4103CE8E3A0EB43274 | **Final.** 23,844 B, 271 LF lines, no CR, no BOM. Read in full. Diff against 581A03DB: [p-2214-16B90FA8/diff-readme.txt](p-2214-16B90FA8/diff-readme.txt) |

Line numbers below are for v2 (924321AE) unless marked otherwise. M = bench/agent8/run/run-matrix.ps1, T = run-timing.ps1.

## Method

1. Full read of v1, then the v1→v2 diff.
2. PS 5.1.26100 `Parser::ParseFile`: 0 errors for v1 and v2. Byte stats: LF/CR/non-ASCII/BOM.
3. Arm-rule replica of `Test-Matrix` ([static5.ps1](static5.ps1), output [static5-out.txt](static5-out.txt), EED28ABB…) over every `matrix*.json` in bench/agent8/run, build/agent4 and build/agent5/w6-draft. Env-key census ([static4.ps1](static4.ps1), [static4-out.txt](static4-out.txt), 03412923…).
4. Interplay with Agent 1's hold manager (build/agent1/hold/hold-manager.ps1, D060F913…, 37 lines, read in full).
5. GO-line format compared with Agent 8's build/agent8/w6-stage/promote-w6.ps1 (57BE63D9…).
6. Installed apps and process names on this PC (Start menu, Appx packages, install folders: [static3-out.txt](static3-out.txt)).
7. Driver path through the runner: M driver lines, T363-376, and the param blocks of run-matrix.ps1 and run-timing.ps1.
8. Rules from SESSION2.md (to L3019 at 22:31) and S4-DRAFT.md.
9. Agent 5's test summaries and console logs in build/agent5/launch-test/results/ (each summary's first line carries the run-night.ps1 hash), and run-tests.ps1 where a test failed. Run-group grep: [t-run-grep-2223.txt](t-run-grep-2223.txt).

## Formal verdict (22:31): SAFE

**SAFE: run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B and README 0058C8F6 can be pinned at 23:30 and double-clicked tonight.**
- **Code:** all three MUSTs and the SHOULD are in: `Stop-Tree` without `taskkill`, the 3-name driver allowlist, the hard stop at 07:30, and `Get-BuildProcs` in `Start-WindowLocked`. Since B0902106 only the `Stop-One` catch has changed (Final section). Also in: must-fix F1, F3 and README L151; should-fix F5; and Agent 10's 1-3, 4's CRLF, and (5)-(8).
- **README:** it matches the code. I read it in full; see the Final section.
- **Tests:** Agent 5's tests on 16B90FA8 pass:
  - go 16/16 (22:18:06);
  - hold 4/4 (22:14:35);
  - run 5/5 (22:22:23);
  - gate 12/13 (22:23:57), plus the t-relaxed re-run. t-relaxed's first run FAILed on the test, not the launcher: with `-StrictMinutes 0.25` and the machine loaded, the third sample came at +0.4 min, after the strict phase, so the expected strict-phase wait line never appeared, and the launcher relaxed correctly at 1.05/0.98/1.10 (all ≤ 1.2 cores, spread 0.12). The re-run PASSES (22:28:05, run-tests.ps1 of 22:25:33 with `-StrictMinutes 1`): "strict gate for the first 1 min" wait lines, then "PASS (relaxed)" at +1 min with 1.02/1.02/1.02.
- **Safety:** nothing in them could harm the user's PC or data, or start a window unsafely.
- **Left open (not safety items):**
  - The RUN-NIGHT.cmd STOP-file smoke test (Agent 10's (4), expect exit 2) is still not seen, so the cmd's first real run would be the double-click. A cmd that fails costs the night, not the PC.
  - Re-hash RUN-NIGHT.cmd after any pin-group run (that group appends a line and then restores the file).
  - Ctrl+C is best-effort (documented).
- **Changes:** any change to these three files after this needs a new pass and a new verdict.

**Verdict so far at 21:55** (kept for the record): the MUSTs are in the code (B0902106); SAFE once the README and the tests match.

The MUSTs (Agent 10 at 21:25, Agent 1 at 21:29, SESSION2 L2910-2913; I agree with all three): `Stop-Tree` without `taskkill /T` (the PassThru kill added in CD64BC93 can reach processes outside the runner's tree through PID reuse: see the (8) row of the CD64BC93/3EFC5312 interim below); the 3-name driver allowlist back on top of the path rule; and the hard stop at 07:30, not 07:45. The README must then match. Agent 1's SHOULD: re-check `Get-BuildProcs` in `Start-WindowLocked`.

**B0902106 (21:42:43) has all three MUSTs and the SHOULD in the code** (see the B0902106 interim below; Agent 10's delta read at 21:48 agrees). Still open: the README lines (R47, R176, R242, R251, R121, R261), test summaries on the final hash (the 21:33 run group failed 3 of 3 on 3EFC5312), and the RUN-NIGHT.cmd STOP smoke test.

Nothing else found could harm the user's PC or data, or start a window unsafely. The driver hole (Agent 10's (5), which I confirmed on my own) lets a matrix get round the launcher's own bin/env/toml rules, so I share Agent 10's condition. My other findings make the launcher refuse windows (F1, F3) or leave programs open (F5); they don't make it misbehave.

## Agent 10's fixes (SESSION2 L2807-2822): status in v2

| # | Fix | v2 |
|---|---|---|
| 1 | Close-Programs: try/catch per process, including WaitForExit | done: `Close-Programs` L462 (process listing in its own try; per-process try/catch with a HasExited check) |
| 2 | HOLD: write only if none exists, delete only ours; a foreign HOLD fails the gate | done: `Set-Hold` L504 (CreateNew, token, read-back), `Sync-Hold` L528, `Clear-Hold` L540. Called at GO (L688), at every gate sample (L599) and right before the start (L626) |
| 3 | Get-Power: a failed query must not count as AC | done: `GetSystemPowerStatus` (L125-129); AC only if ACLineStatus = 1 or BatteryFlag = 128; failed or unknown = not AC (L137-142) |
| 4 | RUN-NIGHT.cmd CRLF, then a STOP-file smoke test (expect exit 2) | CRLF done; smoke-test result not seen yet |

Also in v2: `-NonInteractive` for the runner (L275); the bins' `legodimensions.exe`/`MANIFEST.txt` sha256 logged at GO and compared again at the start (`Get-BinHashes`); leftover REX_*/LEGO_* variables logged at start (L747-748); Roblox Studio off the close list (L38-41); power scheme logged at the start; WARN lines for a missing `sys_csv` and for a `FUNCTIONAL ONLY` plan line; console Quick Edit untouched in dry runs.

## Agent 10's addendum (20:56): my independent check

- **(5) Driver hole: confirmed. I agree it must be fixed.**
  - `Test-Matrix` (L262-267) accepts any driver whose resolved path is a pinned file. It accepts the `{script, args}` object form and never checks the args.
  - `Get-PinFiles` (L163-173) pins far more than drivers: run-night.ps1 itself, RUN-NIGHT.cmd, run-matrix/run-timing/common/timing-env.ps1, winhelper.cs, every top-level *.py/*.cs, drivers\*, and the harness toml and nvml.cs.
  - In run-timing.ps1, T366 starts a non-.ps1 driver directly (file association), and T367 appends `-GamePid N -RunDir R` plus the args.
  - Neither runner script uses `[CmdletBinding()]`, so the unknown `-GamePid`/`-RunDir` land in `$args` and the rest of the args bind normally.
  - Agent 10's fix (plain string `^drivers/[A-Za-z0-9_-]+\.ps1$`, resolved inside `$RunDir\drivers`, objects and args refused) closes it.
  - My census shows every driver path in the matrices above resolves under `drivers\`. Agent 10 reports that all 18 JSONs in bench/agent8/run use plain strings.
- **(6) Started after 07:30, the deadline rolls to tomorrow: confirmed** (`Get-Deadline` L564: `if ($d -le $n) { $d = $d.AddDays(1) }`). I agree: refuse to start when the deadline is more than about 14 h away. This pairs with my F4.
- **(7)** Re-check LogonUI, AC and the desktop after `Close-Programs`, right before the runner: agreed.
- **(8)** Start the runner with `-PassThru` and poll for STOP and deadline + grace: agreed, as recommended. If it is done, it must kill the whole tree (runner, legodimensions, drivers) and log it. Otherwise the documented no-STOP-during-a-window behaviour stays.
- **Note** (separate try for `Set-Awake` and `Restore-Screensaver` in the main finally): agreed.

## Findings (in addition to Agent 10's)

### F1 HIGH, must-fix: the env allowlist refuses every native window and W9

- `$AllowedEnv` (L33) holds only `REX_TIMER_WAIT_BLOCKING` and `LEGO_GPU_WAIT_STATS`. `Test-Matrix` (L254) refuses any other key, with exact case, in any arm of the named matrix.
- Census ([static5-out.txt](static5-out.txt)): every native matrix is refused on env keys alone. `LEGO_NATIVE_FRAME_METRICS` (value `<run>\native-frames.csv`) is set in 47 arms across 11 files, including matrix-native-threaded.json and Agent 4's matrix-repin-native4b*.json. The threaded arms add `LEGO_NATIVE_THREADED`, `LEGO_NATIVE_PREPARE_THREADS`, `LEGO_NATIVE_SNAPSHOT_STATE` and `LEGO_NATIVE_FULL_DRAW_PREPARATION`.
- S4-DRAFT switch column:
  - W8a/#2: `LEGO_NATIVE_SHADER_MISS_CACHE` (L170); `LEGO_NATIVE_RUNTIME_SHADER_CACHE` is at L169.
  - W8b/#21: `LEGO_NATIVE_CHAIN_PRIORITY` (L194).
  - W9/#24: `LEGO_GPU_WAIT_BACKOFF_US` and `LEGO_GPU_WAIT_SPIN_US` (L204), which also names `LEGO_GPU_WAIT_HOOK_GETDATA`.
- These pass as they are: W4, W5 (s3d), matrix-s3-functional, matrix-codegen, and the W6 check matrix (devoff4-bin, cvars only). W7 (#18-#20, cvars) and W10 (#26, a bin) need no env keys.
- **Decision (Agent 1, 21:01): must-fix.** Agent 8 sends the exact key list to Agent 5 by 21:45. Context: SESSION2 L2872 (20:56) says most W7+ functional rows won't run tonight, so the plan is W6 plus windows built only from arms that have already passed their functional checks. W6 passes as it is.
- **Fix:**
  - Add explicit names only, no pattern, so the GO channel stays narrow. Agent 8 confirms the exact keys for the W8a/W8b/W9 arms, and Agent 1 approves.
  - Keep the exact-case check.
  - Make the DRY RUN line "without REX_TIMER_WAIT_BLOCKING / LEGO_GPU_WAIT_STATS" (L637) generic.
  - Update the README env rule and the runner-command text (v1 README L108, L125; 39ECF5C2 L117, L163, L170).
  - Optionally add the new keys to RUN-NIGHT.cmd's `set "X="` lines. The launcher already clears every `$AllowedEnv` key from its own environment at start (L749) and again before each window (L630).
- Agent 8's promote-w6.ps1 L125 has the same two-key list. A W8/W9 promotion tool needs the new list too.
- **Deadline:** before the 23:30 pin freeze. run-night.ps1 is pinned at the double-click, so the list can't change after that.

### F2 (v1 MEDIUM): a window could start without a HOLD. **Fixed in v2**; README L151 must-fix, looks done in 39ECF5C2

- In v1, if the HOLD vanished during the gate wait (for example, the hold manager stale-clearing a stray matrix folder), the launcher did not write it again (v1 L500).
- In v2, `Sync-Hold` writes ours whenever there is none, at every gate sample and right before the start. A foreign one fails the sample and is never replaced. This is the fix I would have proposed.
- README: v1 (01C4D90F) L151 said "If it disappears during the gate wait, the launcher logs that and does not write it again." 39ECF5C2 L202 now says "If its own HOLD has disappeared, it writes it again and logs that." That matches v2; to be confirmed in the full read.

### F3 MEDIUM, must-fix: the 06:45 latest start is not enforced

- SESSION2 L2703: "Every timed run starts by 06:45 and ends before 07:30."
- The launcher only checks estimate + 10 min ≤ 07:30: at GO (L682), in the gate wait (L596) and at the start (L625). So a window estimated at ≤ 35 min can start after 06:45.
- The gate wait can push a start past 06:45 even when the GO was written in time, and Agent 1 can't prevent that by writing the GO earlier.
- **Fix:** a latest start of 06:45, computed like `Get-Deadline`. Refuse a GO read at or after it, give up in `Wait-Quiet` once it has passed, and refuse in `Start-Window` too. Log it and add it to the README's time limits (v1 L140).

### F4 LOW, optional: the "not before 00:00" rule is not enforced

- SESSION2 L2714 and S4-DRAFT (W6 row) say no timed window starts before 00:00. The launcher accepts a GO at any time.
- Agent 1 writes the GO after the user leaves (SESSION2 L2850), so the procedure meets the rule.
- **Optional backup:** a `-NotBefore 00:00` that leaves the GO file unread until then and logs that once. Leaving it unread is better than holding, because no HOLD then freezes the agents before 00:00.
- This can share code with Agent 10's (6) (a start-time sanity window).

### F5 MEDIUM (quality, not safety), should-fix: the close list misses the user's Copilot and Store Roblox

- "Copilot" in the Start menu is the Microsoft.MicrosoftOfficeHub app. Its processes are `copilotapphost.exe` (under `undocked_copilot\`) and `copilotapp_proxy.exe`. No Microsoft.Copilot package is installed, so the list's `Copilot` and `Microsoft.Copilot` match nothing on this PC.
- The Store Roblox app (ROBLOXCORPORATION.ROBLOX) runs as `Windows10Universal.exe`, which is not in the list. `RobloxPlayerBeta`, the %LOCALAPPDATA% player, is.
- **Fix:**
  - Add `copilotapphost` and `copilotapp_proxy`, closed only when the path contains `\WindowsApps\Microsoft.MicrosoftOfficeHub_`.
  - Add `Windows10Universal`, closed only when the path contains `\WindowsApps\ROBLOXCORPORATION.ROBLOX_`. The path check is mandatory, because other Store apps also use the generic name `Windows10Universal`.
  - Reuse the ui32/ui64 pattern (`MainModule.FileName`, falling back to Win32_Process.ExecutablePath).
  - Update the "none of ... running" log line and the README.
- Verified fine: ChatGPT (OpenAI package, `ChatGPT.exe`), Taskmgr, and Wallpaper Engine (`wallpaper32`/`wallpaper64` under steamapps\common\wallpaper_engine). None of these apps was running at 20:38.

### F6 LOW, optional

- There is no way to cancel only the current GO. STOP ends the launcher for the whole night, and no user is there to restart it. Option: a `WINDOW-CANCEL.txt` honoured during the gate wait (drop this GO, keep waiting). Agent 1: not wanted.
- Log total CPU and the top 3 processes for each gate sample. Non-build agent work (python, hashing) is not gated; only the HOLD rule stops it.
- The hold manager (Agent 1's, not the launcher's) exits at 07:30 without clearing, so a window still running at 07:30 would leave a stale HOLD. Agent 1 (21:01): in the morning he clears a stale HOLD, but only if no runner or game is running.
- The display stays on all night (v1 README L20/L47 says so).

## Verified fine (v1, unchanged in v2 unless noted)

- The test hooks (`-StopAt`, `-GiveUpMinutes`, …) are refused without `-DryRun` (v1 L45-47).
- DryRun isolation: GO, HOLD and STOP live in status-dryrun. A dry run closes no programs and leaves the screensaver and keep-awake alone; v2 also leaves Quick Edit alone.
- The mutex blocks a second launcher. The start checks cover the desktop, LogonUI and AC power. STOP is checked at start, while waiting for a GO and during the gate. It is not checked during a window (documented).
- Screensaver: saved, restored in the main `finally`, and an unrestored save is kept. Keep-awake (0x80000003) is released at the end.
- The pins cover everything the runner loads: run-matrix, run-timing, common, timing-env, winhelper.cs, top-level *.py/*.cs, drivers\*, the harness toml and nvml.cs.
- `-PlanOnly` exits before any out dir is made (M434-438 vs M447), so the estimate step can't trip the hold manager.
- The runner splits `-Only` on commas. `-ExecutionPolicy Bypass` matches W5's RUN-WINDOW5-S3D.cmd L25, and the user's double-click is the sanctioned route (SESSION2 L2576-2578).
- GO line: `Parse-Go` (L204) takes 6 tokens, `GO <id> <json> <sha256> only=<arms> repeats=<1-20>`. That matches promote-w6.ps1's `^GO W6 matrix-window6\.json [0-9A-F]{64} only=\S+ repeats=\d+$` (its L64), and an uppercase sha is accepted.
- Hold-manager interplay: the manager overwrites the HOLD once the runner makes its folder, and clears it on summary.md or after 6 min with no game and no writes. With Sync-Hold, the only effect is that a GO waits while the manager still holds a previous window's HOLD (at most about 6 min after an aborted run).
- Agent 5's dry-run tests (20:30-20:39) are in bench/agent5/launch/status-dryrun/ and build/agent5/launch-test/results/.

## Interim: v3 run-night.ps1 163D7659 (21:01:12), read as a diff against v2

RUN-NIGHT.cmd (F7190AB2) and the README (39ECF5C2) are unchanged since v2. Line numbers in this section are v3's.

| Item | v3 |
|---|---|
| Agent 10's (5) driver | **Done** (L37, L272-284). `$AllowedDrivers` = thread-cpu.ps1, io-counters.ps1, pso-stats-at-end.ps1. Only a plain string passes: `-cmatch '^drivers[/\\]([A-Za-z0-9_-]+\.ps1)$'`, and the resolved path must equal `$RunDir\drivers\<name>`, exist and be pinned. Objects, and so args, are refused. [static6.ps1](static6.ps1) on v3 ([static6-out-163D7659.txt](static6-out-163D7659.txt)): all 66 driver uses in the 26 matrix files are those 3 names, so the rule refuses no existing arm. sys-csv.ps1 (in drivers\ but not in the list) is the runner's own sys_csv helper (run-matrix.ps1 L422-424), not an arm driver. |
| Agent 10's (6) 14 h | **Done** (L38 `$MaxRunHours = 14`; start check L795). Side effect: a start before 17:30 is refused too, so the README should say "start it after 17:30". Tonight's ~23:45 start is 7.75 h before 07:30. |
| Agent 10's (7) last checks | **Done** (L656-680). `Start-Window` closes the programs first, then holds the matrix json open with read sharing until the runner ends. `Start-WindowLocked` then re-checks pins, bins, the deadline, the desktop, LogonUI, AC power and Sync-Hold right before the runner. The dry-run guard in Close-Programs is per process (L500), so moving the call is safe. |
| Note: separate try in the finally | **Done** (`Try-Step` L78, L837-841: screensaver first, then HOLD, keep-awake, state). |
| Agent 10's (8) PassThru | Not yet (SHOULD). |
| F1 env keys | Not yet (Agent 8's list is due 21:45). |
| F3 06:45 | Not yet (MUST). |
| F5 apps | **Not met yet.** v3 adds `$CopilotRx` = `\\WindowsApps\\Microsoft\.(Copilot\|Windows\.Ai\.Copilot)_` for the process names Copilot and Microsoft.Copilot (L49-50). Neither package is installed here ([static3-out.txt](static3-out.txt)), so it still closes nothing on this PC. Still needed: copilotapphost and copilotapp_proxy under `\WindowsApps\Microsoft.MicrosoftOfficeHub_`, and Windows10Universal under `\WindowsApps\ROBLOXCORPORATION.ROBLOX_`. `MainModule.FileName` can be denied for packaged apps, so a fallback via Win32_Process.ExecutablePath (QueryFullProcessImageName) is safer. |
| Also new in v3 (all fine) | Unknown arguments are refused (L28). Without `[CmdletBinding()]`, a typo like `-DryRunn` would have run REAL mode. A GO that can't be deleted is refused. Bins are re-hashed after the run, and each post-run check has its own try. Clear-Hold retries 5 times and stops once the HOLD isn't ours. Only this session's processes are closed. Timestamps use the invariant culture. |

**W6 and the follow-up candidates under v3's rules** (static6): Agent 8's staged `build/agent8/w6-stage/test/matrix-window6.json` (BD0696DA, devoff4b-bin, 6 arms) passes every arm rule. So do matrix-window4.json (6CA4AC6E: d0, B, d3, d0t, d11t), matrix-window5-s3d.json (4D7D689B) and matrix-codegen.json (40CF4072), which hold the arms for SESSION2 L2885's follow-up windows. The draft matrix-w6.json (D6388096) fails only on its placeholder bin `build/agent2/S4b-bin-TBD`.

## Interim: CD64BC93 (21:13:38) and 3EFC5312 (21:15:40), read as diffs against v3

RUN-NIGHT.cmd (F7190AB2) and the README (39ECF5C2) are still unchanged since v2. CD64BC93 was read as the full v3→CD64 diff ([p-2114-CD64BC93/diff-run-night.txt](p-2114-CD64BC93/diff-run-night.txt), +138/-41). 3EFC5312 adds only F1 (+5/-1, [p-2119-3EFC5312/diff-run-night.txt](p-2119-3EFC5312/diff-run-night.txt)). Each snapshot was checked with [pass.ps1](pass.ps1): bytes, CRLF, PS 5.1 ParseFile, a grep per item, then [static6.ps1](static6.ps1) under that version's own rules. Both versions parse with 0 errors and are ASCII with no BOM. Line numbers in this section are 3EFC5312's.

| Item | CD64BC93 / 3EFC5312 |
|---|---|
| Agent 10's (5) driver | **Done, and stricter than in v3** (L244, L282-290).<br>- `$AllowedDrivers` is gone. Only a plain string passes: `-cmatch '^drivers/([A-Za-z0-9_-]+\.ps1)$'`. The match is case-sensitive and takes forward slashes only, so a backslash is now refused.<br>- `GetFullPath(Resolve-Driver $dr)` must equal `$RunDir\drivers\<name>`, and that file must exist and be pinned. Objects, and so args, are refused.<br>- Any pinned `drivers\*.ps1` can now be an arm driver, sys-csv.ps1 included. That is acceptable and matches Agent 10's fix as worded: drivers\* are pinned, and sys-csv.ps1 is the runner's own sys_csv helper (run-matrix.ps1 L422-424). Its header (L12-13) says it starts no child process and makes read-only queries, so as an arm driver it would at worst write a second sys.csv into the run folder.<br>- static6 (CD64 rule): all 72 driver uses in the 27 matrix files are forward-slash strings (thread-cpu.ps1 63, pso-stats-at-end.ps1 7, io-counters.ps1 2). No arm is refused for its driver.<br>- **MUST (Agent 10 at 21:25; Agent 1 made it a MUST at 21:29, SESSION2 L2911; I agree):** put the 3-name allowlist back on top of the path rule (thread-cpu, pso-stats-at-end, io-counters). It refuses no current arm, and it keeps out sys-csv.ps1 (the runner's own helper, not an arm driver) and any .ps1 added to drivers\ before the double-click. README R121 must then name the 3 files. |
| Agent 10's (6) 14 h | Done, as in v3 (L43, L896). |
| Agent 10's (7) last checks | Done, as in v3 (L672-697). `Start-WindowLocked` now also checks the latest start (L687).<br>- **SHOULD (Agent 10, 21:25; Agent 1, 21:29, SESSION2 L2912; I agree):** re-check the build processes (`Get-BuildProcs`) there too, as the gate does. |
| Agent 10's (8) PassThru | **Done (SHOULD), but `Stop-Tree` needs a MUST-FIX and the hard stop must move to 07:30** (below).<br>- `Invoke-Runner` (L784-812) starts the runner with `Start-Process -NoNewWindow -PassThru`. Its output goes to `runner-<tag>.out.txt`/`.err.txt` and is tailed into the runner log and the console (`Read-Tail`).<br>- Every second it checks for a STOP file and for the end time + `$GraceMinutes` (15 min) (L789-805).<br>- **MUST (Agent 1, 21:29, SESSION2 L2913): the hard stop is 07:30, not 07:45.** Today it is the end time + 15 min = 07:45 (`$hardEnd`), and README R47, R176 and R242 say 07:45 too. For example, default `$GraceMinutes` to 0, or cap `$hardEnd` at the end time.<br>- `Stop-Tree` (L761-779) runs `taskkill /PID <runner> /T /F`, falls back to `Kill()`, and logs whether the runner is gone.<br>- **MUST-FIX (Agent 10, 21:25; Agent 1, 21:29, SESSION2 L2910; I confirm it):** `/T` follows ParentProcessId with no creation-time check. A process whose parent has exited is therefore taken for a child of whatever later process reuses that PID, at any level of the runner's tree. My read-only census at 21:27 ([pidreuse-check.txt](pidreuse-check.txt), 365 processes) found 9 such orphans, among them explorer.exe, firefox.exe and Discord.exe in the user session. A hit would kill explorer.exe and everything under it, far outside the five approved apps. The fix, as Agent 10 proposes: take one Win32_Process snapshot and walk down from the runner, keeping only children whose CreationDate is at or after their parent's; kill those and the runner. If the snapshot fails, use only `$P.Kill()` plus the build\agent2 legodimensions sweep, never `/T`. Optional hardening: kill the runner first, by its handle, so it can't start the next run (its PID can't be reused while the launcher holds the handle); re-check each target's StartTime right before killing it; and walk once more for late spawns.<br>- In real mode it also kills a legodimensions.exe left over from the window, but only one in this session, under `build\agent2\`, that started at or after the window's start (L766-775).<br>- The `finally` (L806-809) kills the tree if the launcher itself fails while the runner runs.<br>- A STOP during a window is consumed (`Use-Stop`) and sets `$script:StopNow` (L734); the main loop ends on it (L925).<br>- The new test hooks `-StartBy`, `-GraceMinutes` and `-FakeRunner` are in `$hookNames`, so they are refused without `-DryRun` (L62-64). `-FakeRunner` is used only in the DRY RUN branch (L704-712).<br>- `Join-Args` quotes arguments that contain whitespace or `"` (L738). |
| F1 env keys | **Done in 3EFC5312** (L38-43).<br>- `$AllowedEnv` is exactly the 11 keys of build/agent8/w8w9/ENV-KEYS-F1.txt (D1AE6D57…B35C, approved by Agent 1, SESSION2 L2893): same order, same case, no pattern.<br>- The exact-case check is unchanged (L272), and the DRY RUN line is generic (L705).<br>- All 11 keys are removed from the launcher's environment at start and again before each window (L699).<br>- static6 under 3EFC5312: matrix-native-threaded.json (76FE0BAA) now passes every arm. The other native matrices are still refused for keys that aren't on the list (VSYNC, COMMAND_SLOTS, PSO_*, …), as intended.<br>- Still open: the README (R117, R163 and R170 name only the two old keys).<br>- RUN-NIGHT.cmd clears only the two old keys. Adding the rest is optional, since the launcher removes all 11 itself. |
| F3 06:45 | **Done** (L23, L44, L611-616).<br>- `Get-LatestStart` is 06:45 on the morning of the end time, capped at the end time. Dry-run tests use `-StartBy`, else the `-StopAt` time.<br>- It is enforced at GO (a GO read at or after it is refused, L838), in `Wait-Quiet` (gives up, L648) and in `Start-WindowLocked` (L687).<br>- At start, the launcher warns if the latest start has already passed (L913).<br>- The README isn't updated yet. |
| F5 apps | **Done in code** (L51-58, L496-500).<br>- copilotapphost and copilotapp_proxy are closed only from `\WindowsApps\Microsoft.MicrosoftOfficeHub_`, and Windows10Universal only from `\WindowsApps\ROBLOXCORPORATION.ROBLOX_`.<br>- The path comes from `MainModule`, with a Win32_Process.ExecutablePath fallback. A process whose path doesn't match is logged as left alone (L500).<br>- **Approved by Agent 1 at 21:29** (SESSION2 L2914): on this PC "Copilot" is the Microsoft 365 Copilot app (Microsoft.MicrosoftOfficeHub, the only Copilot installed), and the Store Roblox app (Windows10Universal, path-checked) is the player.<br>- README 581A03DB names both, with the path check (R21, R55). |
| README | **Updated at 21:28:05** (581A03DB), read as a diff against 39ECF5C2 ([r-2128-581A03DB/diff-readme.txt](r-2128-581A03DB/diff-readme.txt): 41 lines new, 30 gone). R = 581A03DB's lines.<br>- Now in: the 11 F1 keys (R119, R163, R167, R174); the plain `drivers/<name>.ps1` rule (R121); the 06:45 latest start (R12, R46, R125, R156, R189); the 14 h rule (R23, R242); the close list with the Copilot app, the Store Roblox app and the path check (R21, R55); STOP during a window (R217); the runner's .out/.err files (R175, R234); exit codes 2 and 1 (R238); the new hooks and the `run` test group (R251-253, R258).<br>- To change with the MUSTs: the hard stop (R47, R176, R242 say 07:45); the kill text (R176: `taskkill /T /F`); the driver rule (R121: the 3 names).<br>- Nit: a start before 17:30 is refused too. R23 says only "after 07:30", but "start it in the evening" covers it. |
| RUN-NIGHT.cmd STOP-file smoke test (expect exit 2) | Not seen yet (Agent 10's (4), MUST). |

**W6 under 3EFC5312's rules** (static6):
- These pass every arm rule:
  - Agent 5's real finalize, `build/agent5/w6-draft/matrix-window6.json` (E50D791B, 21:16:51, 6 arms);
  - its check copy (DE34A02A);
  - Agent 8's staged test copy (BD0696DA).
- The template `matrix-w6.json` (now 8440B1E4) is refused only for its placeholder bin, `build/agent2/S4b-bin-TBD`.

## Interim: B0902106 (21:42:43), read as a diff against 3EFC5312

RUN-NIGHT.cmd (F7190AB2) and the README (581A03DB) are unchanged. I read the full 3EFC→B090 diff ([p-2147-B0902106/diff-run-night.txt](p-2147-B0902106/diff-run-night.txt), +89/-27), read L769-874 again in the copy, and ran [pass.ps1](pass.ps1) ([p-2147-B0902106/pass.txt](p-2147-B0902106/pass.txt)): 77,221 B, 1010 LF lines, ASCII, no BOM, PS 5.1 ParseFile 0 errors. Agent 10's delta read (21:48) agrees. Line numbers in this section are B0902106's.

| Item | B0902106 |
|---|---|
| `Stop-Tree` MUST-FIX | **Done** (L769-833). This is the fix Agent 10 proposed, with all three optional hardenings.<br>- No `taskkill` is left in the file.<br>- `Get-Descendants` (L773-793) takes one CIM Win32_Process snapshot (`-OperationTimeoutSec 20 -ErrorAction Stop`) and walks down from the runner, parents first. It follows a child only if its CreationDate is at or after its parent's (L788). The runner's own floor is its StartTime truncated to 1 µs (L810), the precision of CreationDate.<br>- `Stop-One` (L795-802) re-checks right before `Kill()` that the PID's StartTime is within 2 ms of the snapshot's CreationDate (L799). If not, it logs the PID as left alone.<br>- The runner is killed first (L811), so it starts nothing new. `[void]$p.Handle` (L841) keeps its PID from being reused while the launcher runs. Up to 3 walks catch late starts (L813-818).<br>- If the runner's StartTime or the snapshot can't be read, only the runner is killed (L810, L815). Real mode then runs the legodimensions sweep (L820-830, unchanged: this session only, started at or after the window's start, under build\agent2\).<br>- A process with no readable CreationDate is skipped (L776), which errs on the safe side. |
| Driver allowlist MUST | **Done** (L45, L285-294). `$AllowedDrivers` = thread-cpu.ps1, pso-stats-at-end.ps1, io-counters.ps1, checked with `-ccontains` on top of the plain-string path rule (L292). [static6](p-2147-B0902106/static6-out.txt) reads the list (DriverRule v3-list): every driver use in the 26 matrix files is one of the 3 names (thread-cpu 57, pso-stats-at-end 7, io-counters 2). |
| Hard stop 07:30 MUST | **Done** (L24, L843-845). `$GraceMinutes` defaults to 0, so `$hardEnd` is the end time, 07:30. `-GraceMinutes` is still a dry-run-only hook (L65). |
| `Get-BuildProcs` SHOULD | **Done** (L700-703). `Start-WindowLocked` re-checks the build processes, as the gate does. Tests use the fixture's `builds_at_start` list. |
| Also new (fine) | - `-TestFailAfter` (L26, L860) is in `$hookNames`, so it is refused without `-DryRun`. It throws inside `Invoke-Runner`; the catch logs the error and the `finally` calls `Stop-Tree`.<br>- An `$ended` flag (L847-870) makes a Ctrl+C reach `Stop-Tree` in the `finally` too. That path is best-effort: with `-NoNewWindow` the runner shares the console, so a Ctrl+C reaches it as well. Nobody is at the console overnight, and the README's way to stop is the STOP file.<br>- `Log` writes the log files before the console. |
| Unchanged | F1 (exactly the 11 keys), F3, F5, (6) and (7), as in 3EFC5312. |

**W6 under B0902106's rules** (static6): Agent 5's real finalize `build/agent5/w6-draft/matrix-window6.json` (E50D791B) and Agent 8's staged test copy (BD0696DA) pass every arm rule (6 arms each, devoff4b-bin). The template matrix-w6.json (8440B1E4) is refused only for its placeholder bin. 26 files, 8 fully accepted.

**Still open before the formal verdict** (at 21:55; closed by the final files and tests except the cmd smoke test, see the Final section):
- README 581A03DB, to match the code:
  - R47: "If a window is somehow still running at 07:45, it stops that window";
  - R176: "the end time + 15 min (07:45)" and `taskkill /T /F`;
  - R242: "end time + 15 min";
  - R251: `-GraceMinutes` with a default of 15, and no `-TestFailAfter`;
  - R121: should name the 3 driver files;
  - R261 (the `run` test group): should list STOP mid-window, the 07:30 kill, `-TestFailAfter` and the child kill;
  - nit: R23 could say that a start before 17:30 is refused too.
- Test evidence on the final hash. summary-run.txt (21:33, on 3EFC5312) failed 3 of 3: t-run-ok timed out; in t-run-stop the STOP was consumed in the gate wait, so no window started; t-run-deadline never reached "window T1 START". Needed: go, gate and run summaries that carry the final hash and pass, with a normal end, STOP mid-window with the fake child killed, the 07:30 kill and `-TestFailAfter`.
- The RUN-NIGHT.cmd STOP-file smoke test (expect exit 2): not seen yet.

## Final: run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B, README 0058C8F6 (formal pass, 22:31)

I ran [pass.ps1](pass.ps1) at 22:14 against B0902106, F7190AB2 and 581A03DB ([p-2214-16B90FA8/pass.txt](p-2214-16B90FA8/pass.txt)). I read all three diffs and the whole README, and re-hashed the three files at 22:28 (unchanged since 22:12:38). L = 16B90FA8's lines, R = README 0058C8F6's lines.

| Item | Final |
|---|---|
| run-night.ps1, B090→16B9 | +8/-1 ([diff](p-2214-16B90FA8/diff-run-night.txt)), read in full.<br>- Only the `Stop-One` catch changes. If `Kill()` throws, it waits up to 3 s (`WaitForExit(3000)`), then logs `(ended on its own)` or `(NOT killed: <message>)`.<br>- There is no new kill path, and the 2 ms StartTime re-check before each kill is unchanged.<br>- 77,594 B, 1017 LF lines, ASCII, no BOM, PS 5.1 ParseFile 0 errors. |
| RUN-NIGHT.cmd | The only change since F7190AB2 is C15 ([diff](p-2214-16B90FA8/diff-cmd.txt)): `if not "%RC%"=="0" if not "%RC%"=="2" if not "%RC%"=="3" echo The launcher was interrupted (exit code %RC%, e.g. Ctrl+C)...`. CRLF 19/19, no bare LF, ASCII. Fine. |
| README 0058C8F6 | Read in full (271 LF lines, no CR; [diff against 581A03DB](p-2214-16B90FA8/diff-readme.txt)). Every README item open at 21:55 is fixed:<br>- R23: it starts only between 17:30 and 07:30 (the 14 h rule);<br>- R46-47: the night ends at 07:30, and a window still running then is stopped first;<br>- R121: exactly the 3 driver files; sys-csv.ps1 is refused;<br>- R158: the build/game check is in the last checks;<br>- R177-183: the 07:30 hard stop; the runner killed first, by its handle; the creation-time walk, up to 3 times; "There is no taskkill"; the log lines, with "(already gone)", "(ended on its own)" and "(NOT killed)"; the launcher-error and Ctrl+C paths;<br>- R74-77: Ctrl+C and the Terminate-batch-job prompt;<br>- R245: the exit codes, and state.txt after a Ctrl+C;<br>- R249: the hard stop is the end time itself (07:30); a start before 17:30 or after 07:30 is refused;<br>- R258: the test hooks, with `-GraceMinutes` (default 0), `-TestFailAfter <s>` and `-SkipStartChecks`;<br>- R265: the fixture's `builds_at_start`;<br>- R267-271: the test groups. `run` covers a normal end, STOP, the end-time kill, `-TestFailAfter` and Ctrl+C (send-ctrlc.ps1), and checks that the child is killed. |
| `-SkipStartChecks` | Dry-run only, twice over: it is in `$hookNames` (L65), and both uses also test `$DryRun -and $SkipStartChecks` (L697, L962). It has been there since v3. Fine. |
| W6 under 16B90FA8's rules | [static6](p-2214-16B90FA8/static6-out.txt): 28 files, 10 fully accepted (DriverRule v3-list, 11 env keys).<br>- These pass every arm rule: the promoted `bench/agent8/run/matrix-window6.json` (E50D791B, the same bytes as Agent 5's w6-draft finalize), its check copy (77651D94) and Agent 8's staged test copy (BD0696DA).<br>- The template matrix-w6.json (8440B1E4) is refused only for its placeholder bin. |
| Tests on 16B90FA8 | Agent 5's summaries in build/agent5/launch-test/results/; each first line carries the hash.<br>- go 16/16 PASS (22:18:06).<br>- hold 4/4 PASS (22:14:35).<br>- run 5/5 PASS (22:22:23): normal end, STOP while running, end-time kill, launcher error (`-TestFailAfter 25`), Ctrl+C while running.<br>&nbsp;&nbsp;- Each kill logs the runner killed (after the Ctrl+C, "had already ended"), then "killed (walk 1)" with the fake child powershell.exe and its conhost.exe, then "runner stopped: yes". The harness checks that the fake runner and its child are gone ([t-run-grep-2223.txt](t-run-grep-2223.txt)).<br>&nbsp;&nbsp;- The end-time test reaches the same `$hardEnd` path early, with `-StopAt` and a negative `-GraceMinutes`. In real mode GraceMinutes is 0, so `$hardEnd` is 07:30.<br>&nbsp;&nbsp;- `send-ctrlc.ps1` attaches only to the launcher's own hidden console.<br>- gate 12/13 PASS (22:23:57; read at 22:25, since overwritten by the re-run's summary): t-build, t-build-giveup, t-build-start, t-close, t-stop-start (exit 2), t-stop-wait, t-stop-gate, t-unstable, t-toohigh, t-lowres, t-json, t-real.<br>- t-relaxed: first run FAILed on the test, not the launcher: with `-StrictMinutes 0.25` and the machine loaded, the third sample came at +0.4 min, after the strict phase, so the expected strict-phase wait line never appeared, and the launcher relaxed correctly at 1.05/0.98/1.10 (all ≤ 1.2 cores, spread 0.12). The re-run PASSES (22:28:05, run-tests.ps1 of 22:25:33 with `-StrictMinutes 1`): "strict gate for the first 1 min" wait lines, then "PASS (relaxed)" at +1 min with 1.02/1.02/1.02 (summary-gate-relaxed-rerun.txt). |
| Seen after the verdict (not safety items) | - The RUN-NIGHT.cmd STOP-file smoke test (Agent 10's (4)) ran at 22:34 ([smoke-2235-dump.txt](smoke-2235-dump.txt); Agent 5's copy in build/agent5/launch-test/results/smoke-status-2235/). log.txt: `launcher start: REAL; pid 32068`, the start checks (ends 07:30, latest window start 06:45), then START REFUSED for both reasons (not the user's own desktop, and WINDOW-STOP.txt exists), then `launcher end: refused at start, exit 2`; state.txt says refused-at-start. Agent 5 removed the STOP file and status\ afterwards (SESSION2 L3084).<br>- The pin group: 2/2 PASS (22:33). It rewrote RUN-NIGHT.cmd for a few seconds (mtime 22:32:59), and the content still hashes D7A0362B (Agent 10, and Agent 1's re-hash at 22:36; SESSION2 L3056, L3085-3086). |
| Known limits (accepted) | - Ctrl+C is best-effort: with `-NoNewWindow` the runner shares the console. Nobody is at the console overnight, and the STOP file is the documented way to stop.<br>- The walk skips a process with no readable CreationDate (the safe side).<br>- Agent 1's hold manager exits at 07:30 without clearing (F6). Agent 1 clears a stale HOLD in the morning. |

## After the verdict

1. Pin exactly these three hashes at 23:30. A change to any of them after this needs a new [pass.ps1](pass.ps1) run (prevs: [p-2214-16B90FA8](p-2214-16B90FA8/)) and a new verdict.
2. Done: Agent 5 ran the RUN-NIGHT.cmd STOP smoke test at 22:34 (exit 2, both refusal reasons; see "Seen after the verdict"), and RUN-NIGHT.cmd still hashes D7A0362B after the pin group (SESSION2 L3084-3086).
3. W6's GO line (Agent 8, 22:09, SESSION2 L2985) is `GO W6 matrix-window6.json E50D791B… only=s0,p2,p2f,p2fc repeats=5`. static6 passes all 6 arms of that file, so the 4-arm subset passes too. The go group's t-good and t-badgo ×7 cover the GO format.
4. Agent 1's daytime launcher plan (22:25, SESSION2 L2984) adds RUN-DAY.cmd and STOP-LAUNCHER.cmd after the night final, and leaves run-night.ps1 unchanged. This verdict doesn't cover them, so they need their own review before the user uses them. Update 22:38 (SESSION2 L3088-3092): the day launcher is now run-day.ps1, a copy of 16B90FA8 generated by make-run-day.ps1, plus launcher-ctl.ps1, RUN-DAY.cmd, STOP-LAUNCHER.cmd and README-DAY.md, all in build\agent5\day-draft (hashes by ~23:35). Agents 10 and 11 rate them after the windows.
5. GO lines (Agent 1's 22:36 task, SESSION2 L3071): the W9, W5b and W4c lines in Agent 8's PROPOSAL.md (rev 22:35) pass arm rules (1)-(5) under 16B90FA8's own functions, and each promoted copy in bench/agent8/run matches its GO hash; W6's line was re-checked too. All OK at 22:45 ([GO-CHECK.md](GO-CHECK.md), [static7.ps1](static7.ps1), [static7-out-2241.txt](static7-out-2241.txt)). s4b17 passed at 22:41, so W9 runs second (SESSION2 L3096-3102).
