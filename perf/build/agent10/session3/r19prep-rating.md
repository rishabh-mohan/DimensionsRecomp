# #19 chain prep (M7 r19prep): rating

M10, 2026-11-25 06:55 (read-only review plus offline checks at BelowNormal; no builds, no game runs, no markers).

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| r19prep/queue-r19-live.jsonl | 8A6182A9465FDD11 | 10203 |
| r19prep/LAUNCH-R19.md | 88ED92788901820B | 7985 |
| r19prep/r19_path.py | 9D0BE399340483B0 | 3858 |
| r19prep/make_live.py | 6C8583968A8F5D10 | 5927 |
| r19_gate.py (orig 1DD4A89E) | CA5C036CB956BF66 | 13043 |
| check_queue_r19.py (orig 298BB3EC) | EB69D79904C67C4D | 11060 |
| test_r19.py (orig B017F62C) | FAC442EC5B508DC6 | 11054 |

All paths under `build/agent7/session3/`. Hashes match SHA256SUMS-r19prep.txt.

## Base

r19-rows-mp-rating.md (F8ECBC2E), conditions C1-C4 and N1-N5; r19-rating.md (296658C5) (b)3; r19-build-method.md (A813D340).

## Verdict

**SAFE-IF** to launch on M3's queue at ~07:35, if L1-L2 below hold. No BLOCKER. Q1 (pre-authorizing go-r19on): **YES, under the conditions in Q1**.

## What I checked

- Diffs r19_gate.py, check_queue_r19.py and test_r19.py vs `r19prep/orig/`: the changes are only `--bin`, `--j1-info`, `--json` mkdir, SPEC19 i16/g16, Q9 path markers with `unless`, Q10 `--expect-n`, and the matching tests. No changes to the existing gate rules.
- My runs (from WS):
  - `test_r19.py`: SELFTEST PASS 62/62.
  - `check_queue_r19.py r19prep/queue-r19-live.jsonl --expect-n 4`: ALL CHECKS PASS (226); Q10 ready-N = 4.
  - `r19_path.py bin`: READY-R19 OK (MANIFEST 1EBF1163, rexgpu 5DCDD8CB with all 3 needles; devoff4b rexgpu E3CB99CF with none).
- `--bin` on real runs (M7's offline outputs, consistent with the code): s4b01 vs devoff4b-bin PASS; s4b01 vs devoff4b-r19-bin FAIL 2 (bin_dir and rexgpu E3CB99CF != 5DCDD8CB); s4bN4 row i vs devoff4b-bin PASS. So a row run on the wrong bin cannot PASS.
- MANIFEST format: both devoff4b-bin and devoff4b-r19-bin MANIFESTs are `name\tsize\tmtime\tsha256\tsource`, which the parser accepts. devoff4b-r19-bin exe DFBE1D43, rexruntime A33801D1 and TracyClient 85044850 equal devoff4b-bin; only rexgpu differs (r19-build-method C4 holds).
- Chain logic (queue needs/unless + LAUNCH section 1):
  - path N: i, c, g, f need `r19-pathN` and are skipped by `unless r19-path16`; path 16: i16, g16 need `r19-path16` and are skipped by `unless r19-pathN`. Exactly one marker, written once after r19r10, picks the path.
  - i16 PASS writes `r19-ok-i`, g16 PASS writes `r19-ok-g`; c and f are written as `held no-op (C2, path16)`. j needs `r19-ok-g`, so j runs after g or g16. Stop-at-first-FAIL holds because every later slot needs the previous r19-ok marker.
  - Bases match my C2: i16 vs r19r11 (`--row i --n 16`), g16 vs r19r15 with allow-new `d3d12_(async_submit|submit_split)` and `--row j --n 16 --j1-info`. `--j1-info` is used only on g16.
  - i16/g16 drop `ready-N` from needs (correct: fixed at 16 KB, no `<N>`); the mutation test "g16 at <N> -> FAIL" covers it.
- `r19_path.py path`: PASS -> r19-pathN; r19-path16 only for zero fails and exactly one INCOMPLETE, "splits > 0 in the last split line"; anything else -> STOP. `noop` matches C1 points 1 and 3.
- No go-r19on and no r19 markers exist in `build/agent3/session3/` yet.

## Conditions

- **L1** Run `r19_path.py` and every r19_gate call from WS (relative paths). Every #19 ON/OFF row gate includes `--bin` with the bin named in LAUNCH section 2 (B4 for refs, B19 for #19 rows); a row whose gate was run without `--bin` gets no r19-ok marker.
- **L2** Before launch, re-run `check_queue_r19.py <live queue> --expect-n <ready-N>` against the queue file actually installed (not only the r19prep copy) and keep ALL CHECKS PASS.

## Findings

- **SHOULD S1** My C2 memexport restriction (no ON use may set `d3d12_readback_memexport=true` until row f has passed with real splits) is only in the r19f queue note, not in LAUNCH-R19.md. On path 16, f is a held no-op, so the restriction stays in force after the chain. Add one line to LAUNCH section 3 or 5.
- **NIT N1** `r19_path.py path`: path16 also needs `flags == []`. A FLAG (for example the watchdog line) together with "no split at 4 KB" should STOP, not pick path 16.
- **NIT N2** `--bin` checks exe, rexgpu and rexruntime but not TracyClient.dll. It is identical on both bins, so this is low risk.
- **NIT N3** `--bin` compares run.json `bin_dir` by basename only. The hash checks make a wrong bin FAIL anyway.
- **INFO** test_r19 `bin_cases` reads a real run dir (s4bN16) read-only and fails closed if it is missing.

## Q1: may the Overseer pre-authorize go-r19on?

YES. The r19-rating (b)3 intent (no ON row before the OFF #19 rows prove the bin) is kept if all of these hold:

1. M3 writes go-r19on only after r19-ok-a, r19-ok-b and r19-ok-i (from i or i16) exist. Each must come from r19_gate exit 0 with `--bin`, s4b_check clean and a valid run.
2. So far there is no FAIL, no FLAG and no INCOMPLETE other than the planned path16 one.
3. The marker text says "pre-authorized by Overseer <time>" and names the three ok markers.
4. The Overseer can revoke by deleting go-r19on. A row that is already running finishes and is gated as usual.

## Read / Sent

- Read: LAUNCH-R19.md, queue-r19-live.jsonl, r19_path.py, make_live.py, the three diffs, offline-*.out.txt, both MANIFESTs.
- Ran: test_r19.py, check_queue_r19.py, r19_path.py bin (none of them write files).
- Sent: verdict plus sha8 to the Overseer.

## Addendum 09:07: provenance ACK for the post-rating changes (N1, S1)

M10, 2026-11-25 09:07. Overseer request 15:05Z.

| file | rated | now |
|---|---|---|
| build/agent7/session3/r19prep/r19_path.py | 9D0BE399340483B0 | 4629604EB5775935 (3890 B) |
| build/agent7/session3/r19prep/LAUNCH-R19.md | 88ED92788901820B | 2E8287EA5B35A084 (8228 B) |

Both new hashes match SHA256SUMS-r19prep.txt (8FDE4D31).

**Method.** No copy of the rated versions survived under r19prep/, so I rebuilt both from my own 06:52 read of the files. The rebuilt files hash exactly to the rated 9D0BE399 and 88ED9278 (for LAUNCH this needed undoing a cp1252 display artefact in my transcript). I then diffed each against the current file with `git diff --no-index --ignore-cr-at-eol`. Scratch copies are in build/agent10/session3/scratch-final/r19ack/.

**Verdict: ACK.** The changes are exactly my N1 and S1, and nothing else.

- **r19_path.py:** 2 lines changed.
  - The docstring path16 line now reads "no FAIL, no FLAG, and ...".
  - `path()`: `if not j.get('fails') and not j.get('flags') and len(inc) == 1 and inc[0].startswith(NOSPLIT_I)`.
  - The pathN branch (`verdict == 'PASS'` → r19-pathN) comes before it and is byte-identical. So r19r10's pathN decision went through rated code.
  - `noop` is unchanged.
- **LAUNCH-R19.md:** +3 / -0, all in section 3:

  > S1 (M10 r19prep-rating): no ON use (W7 included) may set `d3d12_readback_memexport=true` until row f has PASSed with real splits (`chunks > 0`). On path 16, f is a held no-op, so this restriction stays in force after the chain ends.

  This is S1 as asked. No row, gate, marker or duration line changed.

S1 and N1 are closed. L1 and L2 stand as before.

## Addendum 09:14: #19 S1 ruling: CONCUR with an amendment (S1 restated)

M10, 2026-11-25 09:14. Overseer ruling request 15:08Z (row f does not prove that a memexport readback fired).

**I concur that f PASS does not prove a memexport readback ran under async.** But the premise of S1 (and part of the proposed ruling) is wrong. `d3d12_readback_memexport=true` is already in force in every bench run. S1 as I wrote it restricts a value that every row already uses.

### Evidence (read-only)
- **Harness toml:** `harness/legodimensions.toml` (B763DABB) has `d3d12_readback_memexport = true`, with `readback_memexport_fast/batched/on_demand = false`. The run-dir toml is written at launch (its mtime is the run start). It carries the same line in every r19 run checked: r19r11, r19r10, r19r13, r19r15 and r19r25 (r19r25 has no CLI cvars), and also f10a3/f10b3 and an agent8 matrix run.
- **Code** (snap1 graphics, devoff4bv/r19 overlay, and final/b; the same in all three):
  - `IsReadbackMemexportEnabled(legacy)` returns the d3d12 flag if that flag has a non-default value, else `readback_memexport`. `readback_memexport` is defined with default **true** (command_processor.cpp L111).
  - Either way the result is ON. With fast/batched/on_demand off, every exporting draw takes `IssueDraw_MemexportReadbackFullPath`, which counts `kMemexportFlush`, i.e. "memexport syncs N (KB)" in the slow-frame line.
  - So the CLI cvar in r19r13/r19f is a no-op relative to every other row.
- **W7 arms** s0/s18/s19 and the #19 rows c, d, e, g, j all run memexport readback ON (full path), through the toml and the default. "W7 (readback off)" is not correct.
- **Counter correction:** in f10a3/f10b3 (level-l, slow_frame_log_ms=1, readback ON through the toml) the `memexport full-buffer` field reads `0x (total 0)` in **every** line. 18249 and 52699 is the number of slow-frame lines, not full-buffer events. The non-zero counters are:

  | run | `memexport syncs` > 0 | `readback` > 0 | `on demand` |
  |---|---|---|---|
  | f10a3 | 3987 frames | 12450 frames | 0 (expected, on_demand off) |
  | f10b3 | 5594 frames | 13516 frames | 0 |

  The proof counter is `memexport syncs`, not full-buffer.
- **r19r13** has 0 slow-frame lines because slow_frame_log_ms is unset. It says nothing either way about whether the menu route exports.

### Amended ruling
1. **f PASS** = async + split ran cleanly with readback in its normal ON state. Record the coverage limit in the read-out: it does not show that any memexport sync fired.
2. **S1 restated (S1'):**
   - Drop "no ON use may set d3d12_readback_memexport=true". That value is the bench and harness state in every row, and with the default `readback_memexport=true` it is the effective state without a toml too.
   - Replace it with: "No row has yet *logged* memexport syncs under async. Until a level-route async row with slow_frame_log_ms shows them, the #19 read-out states async + memexport readback as indirectly covered only. The evidence so far: row e runs the level route, where f10 shows syncs in thousands of frames, with readback ON."
   - S1' blocks nothing in the running chain. It does not block W7 either: W7 measures the configuration with readback ON, as it always did.
   - Not to change: do not set `d3d12_readback_memexport=false` anywhere to "keep it off". That would create an untested OFF state.
3. LAUNCH-R19.md section 3 line S1 should be corrected to S1' after the chain, not mid-chain. It is not a gate input.

### Follow-up row r19eL (optional, not for the running chain)
- **bin:** build/agent2/devoff4b-r19-bin.
- **route:** build/agent3/toypad/routes/level-l.txt (6F9E6009), toypad true, -Seconds 600.
- **cvars:** `framerate_limit=0;d3d12_submit_split_kb=<N>;d3d12_async_submit=true;d3d12_readback_memexport=true;slow_frame_log_ms=1`. The readback cvar is redundant with the toml, but it puts the state in run.json.
- **ref (optional, for s4b_check NEW/MORE):** the same with devoff4b-bin and without `d3d12_async_submit`.
- **PASS conditions, all required:**
  1. Clean run: exit 0, no WER/dialogs/dumps, wm_close and "Title terminated" once, steps 119/119 and stopped_by_script.
  2. Timeouts only on the level-l by-design wait lines (final_gate v3 map, ≤ 31). 0 of final_gate's 10 bad strings. No hang (hang = FAIL).
  3. `r19_gate --row e --n <N> --bin devoff4b-r19-bin` PASS on the **joined, rotated** logs. slow_frame_log_ms=1 writes ~20-55k lines, so check that the gate reads every game*.log.
  4. The run-dir toml has `d3d12_readback_memexport = true` and fast/batched/on_demand = false.
  5. Summed over the slow-frame lines: `memexport syncs` count > 0 and KB > 0. The f10 level runs had it > 0 in about 4-5.6k frames. 0 → HOLD (the route did not export): do not PASS, ask.
  6. `memexport full-buffer` is not a criterion.
- **Effect:** PASS lifts S1' (async + memexport readback directly covered).
- **Cost:** ~10 min of queue time; functional only. slow_frame_log_ms also enables NoteMemexportRange bookkeeping (L3086), so its timing is meaningless.

### Correction to my earlier rating
S1 (r19prep-rating, 06:55) assumed that readback was off unless the cvar was set. It is on in every row, so S1 as written was ill-posed. S1' above replaces it. N1, L1 and L2 are unaffected.

## Addendum 09:20: #19 debug-layer validation follow-up pair (r19vr / r19vg)

Overseer request 15:14Z. Not for the running chain. **Verdict: SAFE-IF H1-H6** (harness conditions below). The pair spec is sound as a functional check, with the coverage limits stated.

### Code facts (read, not run)
- `ui/d3d12/d3d12_provider.cpp` (snap1, 37654752):
  - L23 `d3d12_debug` (kInitOnly).
  - L26 `d3d12_break_on_error` and L29 `d3d12_break_on_warning`. Both are read once, at device creation (L391/L395), so they are init-only in effect.
  - L361-399: the ID3D12InfoQueue comes from `QueryInterface` on the device, which succeeds only with the debug layer on. So **break_on_error does nothing without `d3d12_debug=true`**.
  - The storage filter denies INFO severity and 6 IDs: EMPTY_LAYOUT, RT_FORMAT_MISMATCH_PSO, RTV_NOT_SET, EMPTY_SCISSOR, and the two clear-value mismatches. break_on_error arms CORRUPTION + ERROR.
  - There is no GetMessage or callback anywhere. Only the D3D12 queue is configured: no DXGI info queue, no GPU-based validation.
- **A break** = the debug layer raises EXCEPTION_BREAKPOINT (0x80000003) in the thread that made the bad call. Only the **first** error is seen; the process dies on it.
- `core/exception_handler_win.cpp` (8817AD1E):
  - The VEH `ExceptionHandlerCallback` (L46-111) handles only ILLEGAL_INSTRUCTION and ACCESS_VIOLATION. `default:` returns CONTINUE_SEARCH (L84-86). So a breakpoint is **not swallowed**.
  - The icon_probe VEH (`rexlego/src/icon_probe.cpp` L223-296) handles only GUARD_PAGE and its own SINGLE_STEP. Everything else is CONTINUE_SEARCH.
  - The break therefore reaches `LastChanceExceptionFilter`, which:
    - logs `[FATAL] Unhandled exception 0x80000003 at host ...` and `[FATAL] That is <module>+0x<off>`;
    - writes `crash-<pid>.dmp` in the run dir and logs `[FATAL] Minidump written to ...` (one of final_gate's bad strings);
    - returns CONTINUE_SEARCH, so **WER / AeDebug follows**.

### Pair spec (menus route, parity with r19r15 / row g)
- **r19vr (ref, run first):**
  - bin `build\agent2\devoff4b-bin`, `-Seconds 420`;
  - input `harness\routes\b-gate-menus-long.txt`;
  - cvars `d3d12_debug=true;d3d12_break_on_error=true;d3d12_submit_split_kb=<N>`.
- **r19vg (#19, only after r19vr has been read):**
  - bin `build\agent2\devoff4b-r19-bin`;
  - the same args and cvars, plus `d3d12_async_submit=true`.
- **Optional L variants**, to cover row e's paths:
  - the same pair on `build/agent3/toypad/routes/level-l.txt` (6F9E6009), toypad true, `-Seconds 600`, with `framerate_limit=0` added.
  - Only if the menus pair is clean.
- `<N>` = the chain's decided split value, the same one as r19r15 / g.

### PASS (each run)
1. Clean exit:
   - exit 0, close_method wm_close, wer_seen false;
   - 0 Application events (1000/1001/1002/1026), 0 `*.dmp` in the run dir and in CrashDumps.
2. No `[FATAL]` line and none of final_gate's bad strings, `Minidump written to` included.
3. The DRED line appears once, and there is no `Failed to enable` WARN (debug layer active).
4. Steps 54/54 and stopped_by_script (L variants: 119/119 and stopped_by_script, timeouts only on mapped by-design lines).
5. run.json cvars show `d3d12_debug=true` and `d3d12_break_on_error=true`. **Without these, the run does not count.**
6. r19vg only: `r19_gate --row g --n <N> --bin devoff4b-r19-bin` PASS (async init, chunks > 0, failed = 0) on the joined logs.

What a PASS proves: on the covered route, no D3D12 ERROR/CORRUPTION message was **stored**, outside INFO and the 6 denied IDs. It covers CPU-side validation on the D3D12 queue only; DXGI and GPU-based validation are not covered.

### Reading a break
- **Signature:**
  - process exit code 0x80000003 (-2147483645);
  - game.log `[FATAL] Unhandled exception 0x80000003` plus a `That is <module>+0x<off>` line (expect D3D12SDKLayers.dll / D3D12Core.dll);
  - `crash-<pid>.dmp` in the run dir;
  - wer_seen true and/or close_method killed; the harness exits 1.
- **Break in r19vr (old bin, no async)** = a pre-existing validation error, **not #19**.
  - Then r19vg cannot be judged at this setting: do not run it, and open a separate item.
  - The pair can only resume once the pre-existing error is fixed or added to the deny list in a separate, rated change.
- **Break in r19vg with a clean r19vr** = a **#19 suspect**. #19 FAILs on validation coverage; this does not touch W7 timing results already taken.
  - Triage from the dump: the faulting thread's stack (D3D12 Submit worker vs GPU Commands thread vs a split-submit point).
  - The message text is **not** in game.log. It needs a debugger or a DebugView-type OutputDebugString capture on a rerun. Both are manual and out of the harness.
- **Same signature in both** = pre-existing (as for r19vr).
- A break catches only the first error. A clean run is "no stored ERROR on this route", not "no errors anywhere".
- **A hang** (no exit, killed at the close timeout, no `[FATAL]`) is not a validation verdict. Read it as a harness/WER-path problem (see H3), not as PASS or FAIL for #19.

### Positive-control limit
- No log line confirms that break_on_error is armed. A clean run could therefore be vacuous if, for example, the cvar name were not applied. run.json (PASS item 5) shows intent, not effect.
- **Optional control, r19vw:** the r19vr args with `d3d12_break_on_warning=true` added and `-Seconds 120`, on devoff4b-bin.
  - WARNING severity is stored (only INFO is denied), so a break there proves both the arming path and the harness break path end to end.
  - No break means the arming is unproven. Report that as a limit; it is not a failure.
  - Run r19vw **first** if you want the harness break path tested deliberately, rather than by surprise in r19vr. It is the run most likely to raise the dialog risk in H2.
- **Better long-term fix (recommendation, separate rated change):** a small SDK logging patch that drains the info queue into game.log, either by `GetNumStoredMessages`/`GetMessage` at frame end, or by `ID3D12InfoQueue1::RegisterMessageCallback` where the runtime has it. It logs severity, ID and text, never breaks, and counts every message, not just the first. That turns "no break" into "0 messages counted" and removes the WER path entirely.

### Harness safety (my view: the break path is untested in practice, so H1-H6)
Facts:
- `harness/run-game.ps1` (C2533FDF) runs the game on a hidden desktop.
  - Every 2 s it polls for WerFault/WerFaultSecure with `-p <gamePid>` → wer_seen → it leaves the loop.
  - It closes with WM_CLOSE, then Kill after CloseTimeoutSec (60). It does not kill WerFault.
- No run under `build/agent3/runs` has wer_seen / killed / an early exit, so this path has never been exercised.
- Registry (read only):
  - HKLM WER has no `DontShowUI`; HKCU WER is empty; there is no LocalDumps key;
  - **HKLM AeDebug `Debugger` = vsjitdebugger.exe, with no `Auto` value**.
  - So an unhandled breakpoint may show a WER "close / debug" dialog or a VS JIT prompt. That holds the dying process until someone answers or the harness kills it.

Conditions:
- **H1:** hidden desktop only. Never run a break-capable row on the visible desktop or outside run-game.ps1.
- **H2:** before the first break-capable run (r19vw or r19vr), the Overseer or the user confirms that a WER/JIT prompt raised for a hidden-desktop process cannot appear on the user's visible desktop, or accepts that risk. vsjitdebugger may run in the interactive session, and I cannot verify that from here.
  - Do **not** change AeDebug/WER registry values to work around it: that is outside scope, and only the user may decide it.
- **H3:** after any run that broke, before anything else runs:
  - list WerFault/WerFaultSecure/vsjitdebugger processes;
  - stop **only** those whose command line carries `-p <that run's game pid>`, and confirm that the game pid is gone;
  - touch no other process.
  - If the game pid is still alive after the harness kill, stop and report. Do not queue the next row.
- **H4:** a free queue only: after the #19 chain and the #33 rows, like r19eL. Never inside a user timing window or a confirm window: a WER dialog and a dump write disturb the machine.
- **H5:** not chained. A break run's exit 1 must not write, or be read as, any chain marker. Each run is read by hand against the PASS list above.
- **H6:** the gates read the joined, rotated game*.log (L variants), and the dump file is kept in the run dir for triage, not deleted.

### Effect
- A clean r19vr + r19vg pair (plus the r19vw control, or its limit stated) upgrades ref 4 / row g from "runs clean with the debug layer active" to "no stored D3D12 ERROR/CORRUPTION under async on the covered route".
- Until then, the coverage limit the Overseer ruled stands in the #19 read-out.
