# Final-build rating: D2 (rexruntime extension / build driver), D3 configure delta, S1 fix

M10, 2026-11-25 ~07:25 (request 13:20Z). Read-only review. I ran no compiler, ninja or build. My one run: `check-defaults.py` on a real win3 log.

## Files rated (build/agent2/final/)

| file | sha256/16 | bytes |
|---|---|---|
| build-final.py | 740E59450887B338 | 22261 |
| prep-final.py | 83F732CA9CEB301F | 15823 |
| pe-check.py | F4368C32076AAA3E | 6562 |
| pe-diff.py | FF5C661C21D7D330 | 3109 |
| BUILD-STEPS.md | EE079AFEAB4F9779 | 14636 |
| BUILD-PLAN.md | B0A3B9F6F88FC9DD | 10786 |
| check-defaults.py | D9936C56C5E04B98 | 8698 |
| fsyntax.py | E9E4E131D04177C5 | 6956 |

Unchanged and not re-rated: recompile.py 855BCC79, relink.py F3C6EEAF, stage-variant.py D2BD1C63, verify-bins.py 80FF4C5F, mapcheck-s4c.py F8CB7B49.

Base: final-defaults-rating.md (C20B6FDB), D1-D7, F1-F7, S1. FINAL-DEFAULTS.diff 955543F5.

## Verdict

- **D2 (build-final + prep-final + pe-check + fsyntax): SAFE-IF**, conditions B1-B3.
- **D3 configure delta: SAFE-IF**, conditions B4-B5.
- **S1 fix (check-defaults xenos/legacy full back-off line): CONFORMS.**
- No objection to step 0 (`prep-final.py`) or step 1 (`fsyntax.py`) now. Legs may start once the build slot opens.

## What I checked

**D2 method**
- The rt leg reruns the snap1 `rexruntime.dll` edge from `snap1-sdk/build-Release.ninja` with no change to recompile.py or relink.py.
- relink.py fails when a swap target matches anything but exactly one explicit input (L309 `matches %d explicit inputs (need 1)`). It also fails unless there is exactly one edge (L288).
- Replacement objects are placed in the out dir under their own basename (L315-326). prep-final requires the basenames to be unique, which fixes the lld /MAP basename keying.
- Every leg with its own CTL (rt, gpu, xe, nat) recompiles the unpatched snap1 TUs with the build's own flags and relinks with `--compare` (plus `--compare-map` for exes). It STOPs before ON unless the compare (and map) line is PASS.
- xeoff/natoff require the xe/nat `build-final.txt` RESULT: PASS. Output dirs must be new, `--jobs` is ≤ 8, and the HOLD file is checked.
- **PCH reuse is sound here.** 5 of the 9 SDK TUs use `-include-pch` with the snap1-sdk `cmake_pch.hxx.pch` (runtime, xmemory, xobject, xthread, shared_memory).
  - The 11 patched files are all `.cpp`, so no patched header can hide behind a stale PCH. The PCHs include standard headers.
  - The PCHs are read, not rebuilt.
  - Same method as devoff4bv/r19 (shared_memory.cpp, CTL PASS). The compile logs there contain no "pch"/"error" text, so the log gate does not false-fail on command echo: recompile.py logs only compiler output.
- **pe-check (D5):**
  - Exports must be equal by name.
  - Imports are compared per DLL, normal and delay-load, by name or ordinal. Without `--allow-add`, every DLL's import list must be unchanged with no duplicates. So rt `pe=[]` = exports equal + all imports unchanged, which is D5 for rexruntime.
  - gpu: `--allow-add` GetFlagByName/GetFlagSource needs exactly 2 added names, each matching one substring, with no removals. `--ref-count rexruntime.dll=115` and `--added-exported-by` devoff4b rexruntime are also passed. Correct.
- **Gates per leg:**
  - rt: needles `Final defaults:{}` (in ON, not in ref).
  - gpu: `Final defaults (GPU): {} {}`.
  - xe: q500 MARK in ON and not MC.
  - nat: MC + FP_NEW in ON, and not FP_OLD or MARK. The gen-on `-I` must precede `snap1-on/generated` in every command.
  - All legs: no overlay path bytes; shared DLL E3CB99CF before and after; ON output differs from the ref.
  - Stage: atomic stage-variant, verify-bins on the new bin + 3 shared bins, TracyClient check, nativefinal DLLs A33801D1/E3CB99CF, no `cache/`.
  - This matches BUILD-STEPS steps 2-5 and D1/D5/D6.
- **fsyntax:**
  - It builds the exact ON commands via `recompile.py --dry-run`, drops `-o <obj>`, adds `-fsyntax-only` and re-checks for output flags.
  - Logs go only under `b/fsyntax/`. `-include-pch` is read-only.
  - Sets: rt 8, gpu 1, xe 1, xeoff 1, nat 4 (shaders.cpp included, snap1-on flags, gen-on first), natoff 4 = 19. D4 is met.

**D3 configure delta**
- snap1-sdk `CMakeCache.txt` has `CMAKE_C_FLAGS` = `CMAKE_CXX_FLAGS` = `-march=x86-64-v2` and `*_RELEASE` = `-O3 -DNDEBUG`. It has no compiler launcher. No snap1-sdk ccdb command has a prefix map today.
- So the delta keeps the base flags byte-equal and adds only `-fmacro-prefix-map=<fb>=<snap1>`. That affects only `__FILE__`/`__builtin_FILE` expansions, and its purpose is to make them equal to the reference.
- The same `CMAKE_INSTALL_PREFIX` string without `cmake --install` writes nothing there.
- **pe-diff:**
  - It requires equal file size.
  - It lists every differing range and allows only COFF/export/debug-entry TimeDateStamp fields and debug-dir data. Anything else (including the optional-header CheckSum, if set) is OTHER, and the exit is 1.
  - A range that straddles a field boundary also counts as OTHER, so the check fails closed.

**S1 fix**
- check-defaults `L_BO_ON` is the full line `GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built.` (exact match). xenos and legacy require it exactly once, require 1 back-off line of any kind and 0 OFF lines.
- M2's `work/test-check.py` has synth cases `xenos-stats-on`, `xenos-no-getdata-hook` and `legacy-stats-on`, all expected FAIL. I read it but did not run it, because it writes into M2's dir.
- My run: `check-defaults.py build/agent8/matrix/20261125-0315/runs/0319-win3-r1/game.log --mode legacy`: **RESULT PASS**, with all 6 proof lines and 0 bad strings.

## Conditions

- **B1 (D2):** run in the order step 0 PASS → fsyntax PASS → rt → gpu → xe → nat → stage, exactly as BUILD-STEPS lists.
  - The per-leg CTL compare is the proof. A non-PASS gate means STOP: stage nothing and report. No re-running a leg into a reused dir, and no hand edits to `b/`.
- **B2 (D2):** the PCH reuse stays valid only while every patched file is a `.cpp`.
  - If any header joins the diff, PCH reuse is invalid. That would mean a new rating, or the D3 path.
- **B3 (D2/D3):** the D3 manual path (copying fallback DLLs into `b/rt/link-on`, `b/gpu/link-on` and writing a PASS log there) must not be staged until the Overseer and I have seen the pe-diff output and the hand-run needle and pe-check output.
  - The PASS log must quote those outputs verbatim.
- **B4 (D3):** fallback only if a step 2 CTL fails because of the method. Build in a fresh `final/fb` copy (hash-verified, no `out/`), and never run `cmake --install`.
  - The **unpatched** fb build must give `pe-diff` RESULT PASS against devoff4b `rexruntime.dll` A33801D1 **and** `rexgpu-xenos.dll` E3CB99CF before any patch is applied.
- **B5 (D3):** the configure command must be the delta as written: `-march=x86-64-v2` plus the one prefix map, the same preset and cache options, no launcher.
  - Record the fb `CMakeCache.txt` `CMAKE_*_FLAGS*` lines in the report so they can be compared with snap1-sdk's.

## Findings

- **SHOULD S1 (fsyntax):** gate the per-set TU counts (rt 8, gpu 1, xe 1, xeoff 1, nat 4, natoff 4 = 19).
  - Today a set whose `recompile-commands.txt` yields 0 commands still ends PASS. prep-final's list checks cover this indirectly, so it is not blocking.
- **NIT N1:** the `pch|error` log regex (case-insensitive) fails closed on any benign warning text containing "error" or "pch". Expect a possible false STOP; read the log before treating it as real.
- **NIT N2:** CTL compiles snap1 sources without the prefix map, while ON compiles the overlay with the map.
  - So CTL proves flags + link, not the overlay remap itself.
  - The remap residual is covered by the "no overlay path bytes" gate, the needle gates, and the devoff4bv/r19 precedent.
- **NIT N3:** the xe mapcheck s4c ref is the `devoff4-bin` map, not devoff4b.
  - This is the established s4c reference (31 aliases). CTL already compares the map with devoff4b's. Info only.
- **NIT N4:** the BUILD-STEPS hard rule "write only `b/` and new bin dirs" omits `final/fb/` for D3. Add it if the fallback is ever used.
- **NIT N5:** hard-coded VS ninja/cmake paths in prep-final. Info only.

## Read / Sent

- Read: the 8 files above; recompile.py `--fwd-src`/log handling; relink.py L159-326, L405-414; FINAL-DEFAULTS.diff file list (11 `.cpp`); snap1-sdk CMakeCache flags; snap1-sdk ccdb pch flags for the 9 SDK TUs; the snap1-off/on ccdb for the 5 game TUs (no pch); the `cmake_pch.hxx` heads; devoff4bv/r19 log-ctl/log-on logs; `work/test-check.py`.
- Sent: verdict + sha8 to the Overseer.

## Post-rating edits (M10, ~07:32; request 13:31Z): CONFORMS

- **Diffs verified.** Reversing each diff on a scratch copy of the current file gives exactly the hash I rated:
  - build-final.py 5BE1F221800137BD, reversed with diff F5B111B2, gives 740E59450887B338.
  - fsyntax.py 66C7D74022A068DA, reversed with diff 84AFD255, gives E9E4E131D04177C5.
  - So nothing else changed. Scratch copies were deleted.
- **build-final freshness gate: fails closed.**
  - A real run leaves the output in `link-on/<out>` or `link-ctl/<out>`, so a later real run is blocked. That holds even after a failure: a leftover CTL output blocks until the operator clears it.
  - `relink.py --dry-run` writes only `relink-command.txt` and `relink-rsp-content.txt` (L365-376: "dry run: not linking"). A dry-run leftover therefore never creates the output file and can't pass as a built file.
  - The later `ON relink` gate still requires rc 0 plus the file.
  - Residual: a stale `.map`/`relink.log` from a failed earlier link (no output file) is overwritten by the new link of the same command. Info only.
- **fsyntax S1: CONFORMS.**
  - `WANT_N` is rt 8, gpu 1, xe 1, xeoff 1, nat 4, natoff 4 (= 19).
  - A count mismatch is added to `fails` before the commands file is written. Both the dry-run and the real run then end FAIL and compile nothing.
