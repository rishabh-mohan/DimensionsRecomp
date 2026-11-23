# run-timing.ps1 -InputScript port (Agent 3 -> Agent 8)

Status 2026-11-22 06:12: built and tested **without a game**. **Not applied.**
- `bench/agent8/run/run-timing.ps1` belongs to Agent 8. Apply after window 4 (runner freeze).
- `harness/vpad/vpadhost.cs` belongs to Agent 3. The reset patch goes in after 07:15 if Agent 1 OKs it.

## Files (build/agent3/patches)

| file | what | sha256 |
|---|---|---|
| `run-timing-inputscript.patch` | unified diff for `bench/agent8/run/run-timing.ps1`: 15 hunks, +82/-3, LF | - |
| `run-timing.ps1.patched` | the full patched runner: 826 lines, LF, ASCII, no BOM | `2E99CDDBEC70B06FAEFC9CE5839B20DB7C4EBBC50831740350879E838E1018DF` |
| base: `bench/agent8/run/run-timing.ps1` | the current runner: 747 lines, mtime 03:30:01 | `75F4B5278BD75C1452CED72D5CE746708D048E5E4357B01BA3C69EF20D19D6D3` |
| `vpadhost-reset.patch` | `harness/vpad/vpadhost.cs`: adds `ResetRun()`; 3 hunks, +30/-1 | - |
| `vpadhost.cs.patched` | the full patched host: 544 lines | `2015C3743C99CF5698411DB468F8BCDACE49E4C49EAFC90AEA982A0092CA2E8B` |
| base: `harness/vpad/vpadhost.cs` | the current host: 515 lines | `39AA9C4670A23354756479A87465056CD48F18EB9973F2DF04D7E6B091BF0C27` |

The pad DLL is not changed by this work. It is the gate copy `build/agent3/vpad/xinput1_4.dll`, sha256 `309DF316B576D2C39715D1C2B6803F34AB92F1FAFC84315D2B65483159AC7B3B`.

## Apply (from the repo root)

    git apply --check build/agent3/patches/run-timing-inputscript.patch
    git apply build/agent3/patches/run-timing-inputscript.patch

Alternative: if `Get-FileHash bench\agent8\run\run-timing.ps1` still gives the base sha above, copy `run-timing.ps1.patched` over it.

If the runner has changed since 03:30 and the patch no longer applies, ask Agent 3 to rebase it.

Quick check after applying (no game starts and no run dir is created):
- `... run-timing.ps1 -InputScript harness\routes\attract-long.txt -MinFreeRamGB 999` should pass the input checks and stop at the RAM check (exit 3).
- `... run-timing.ps1 -InputScript build\agent3\test\vpadreset\bad.txt` should exit 1 with `!!! INPUT SCRIPT: ...bad.txt:1: unknown command 'bogus'; game not started`.

## Use

    powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-timing.ps1 -BinDir build\agent2\devoff3-bin -Tag attract-devoff3 -InputScript harness\routes\attract-long.txt <your window args: -WarmupFrom firstframe -Warmup .. -Seconds .. -SysCsv -MinWindowAfterFirstFrame .. -SeedCache ..>

- `-VPadDll` defaults to `build\agent3\vpad\xinput1_4.dll`.
- Use the same script and DLL on both arms of a pair. With the pad DLL, the game's XInput polls read a memory-mapped file instead of going through the system DLL, so both arms need the same input path.
- `attract-long.txt` reaches its `stop` at about launch + 470-490 s. With a shorter window the steps are simply halted when the loop ends.

## What the patch does

1. **Checks before the RAM check and before the run dir exists.** Each failure exits 1 with `!!! INPUT SCRIPT: <reason>; game not started`:
   - the script is missing;
   - the DLL is missing;
   - the bin dir has its own `xinput1_4.dll` (REFUSED);
   - the script fails `[Agent3Input]::Load` (the message gives `file:line`);
   - the pad host was already used in this powershell.exe and this vpadhost.cs has no `ResetRun`.

   `vpadhost.cs` is compiled with Add-Type once per process. If `ResetRun()` exists it is called first, and an error from it also exits 1.
2. **Log-flush note (not a failure).** If the script has `wait_log` steps and no `-Cvar log_flush_interval=...` is given, the runner prints a note. `run-game.ps1` passes `--log_flush_interval=1` but `Get-GameArgs` does not. `attract-long.txt` has no `wait_log`.
3. **Setup after `Get-GameArgs`:**
   - calls `Start(script, <run>\vpad-state.bin, <run>\input.csv, <run>\game.log, <run>\perf.csv)`;
   - copies the DLL to `<run>\xinput1_4.dll`, never into the bin dir;
   - adds `--input_backend=xinput` unless an arg already sets `input_backend`;
   - sets the env var `AGENT3_VPAD=<run>\vpad-state.bin`;
   - prints a console header line.
4. **Clock.** `Go($sw.Elapsed.TotalSeconds)` runs right after the process starts, so `input.csv` `t_s` is on the runner clock with 0 = process start.
5. **Loop.** Each step change is appended to the proc.csv note (`input <status>`). A script `stop` is noted (`input script stop`, plus a console line) but does not end the run; the window decides the end.
6. **End.**
   - After the loop, `Halt()` stops the steps and writes a neutral pad. It also runs in `finally` on an error or interrupt.
   - After the game has exited, `Finish()` adds its counters to run.json `input_script`. If `Finish()` fails, that is a problem.
7. **New problems** (status PROBLEM, exit 1):
   - `INPUT SCRIPT ERROR: ...`
   - `INPUT SCRIPT: N wait step(s) timed out (script lines ...)`
   - `INPUT SCRIPT: the game never read the virtual pad (pad_reads 0)`
8. **Outputs.**
   - summary.txt gets an `input` line: steps done/total, last step, timeouts, pad reads and active reads.
   - run.json `input_script` gets:
     - the script and its sha256;
     - the DLL source, the DLL copy and its sha256;
     - the state file and input.csv;
     - the `Finish()` counters: steps_total/done, last_step, timeouts, timeout_lines, stopped_by_script, error, dll_loaded_by_pid/from, dll_maps, pad_reads, pad_active_reads, caps/key/set_state/enable calls, key_events, perf_rows_seen, perf_locked, perf_bytes_at_end, log_lines_seen.
   - run.json `params.input_script` and `params.vpad_dll` keep the values as given.
9. **No system input** (no SendInput or PostMessage), so the `-SysCsv` input flags are unaffected.
10. **Strict mode 2:** every new variable is set unconditionally, and the `Finish()` keys are read by index.

## In-process caveat (run-matrix.ps1)

`run-matrix.ps1` runs run-timing.ps1 inside the same powershell.exe, and `[Agent3Input]` is static. With today's vpadhost.cs, the second `Start()` in a process runs no steps and reports the first run's counters; the host test below shows this.

The patched runner refuses that case: exit 1 before anything is created, with the message `the pad host was already used in this PowerShell process ... run each -InputScript run in its own powershell.exe`.

`vpadhost-reset.patch` adds `ResetRun()`, which:
- stops and joins the worker;
- closes csv, view, map and file;
- zeroes the pad;
- resets the clock, tails, perf fields, rings and all counters.

`Start()` calls it first and the runner calls it during its checks, so every in-process run starts clean. Until it is applied, use **one -InputScript run per powershell.exe**.

## Tests (06:08, no game launched, no run dir created)

- The PowerShell parser finds 0 errors in the patched runner and in the test hosts `build\agent3\test\rtpatch-hostA.ps1` and `rtpatch-hostB.ps1`.
- **Host A** runs the patched copy `build\agent3\rtpatch\run-timing.ps1`. All six cases pass and no run dirs are created:

  | case | input | result |
  |---|---|---|
  | T1 | missing script | exit 1 |
  | T2 | bad script | exit 1, `bad.txt:1: unknown command 'bogus'` |
  | T3 | bin dir with an `xinput1_4.dll` | exit 1, REFUSED |
  | T4 | missing DLL | exit 1 |
  | T5 | valid `attract-long.txt` | passes the checks, exit 3 at the RAM check (`-MinFreeRamGB 999`) |
  | T6 | no `-InputScript` | exit 3, unchanged path |

- **Host B** does two runs in one process with `build\agent3\test\vpadreset\mini.txt`:
  - With the original vpadhost.cs, run 1 does steps 5/7 and writes 9 input.csv lines. Run 2 is a no-op: 3 lines and stale counters 5/7. The patched runner then refuses with exit 1 and the in-process message.
  - With the reset vpadhost.cs, runs 1 and 2 are identical (5/7, 9 lines), and the runner passes its input checks (exit 3 at the RAM check).
- `git apply --check -v` exits 0 for both patches against the current files (base shas above).

**Not tested:** a real game run through the patched runner. That is Agent 8's self-test after window 4.

The host side is already proven by `harness\run-game.ps1 -InputScript`: attract run `build\agent3\runs\20261122-052024-attract-devoffB` did steps 91/91, pad_reads 10485, perf_locked True. Only the runner glue is new.
