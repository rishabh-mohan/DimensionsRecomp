# final_gate.py (F1-F7 ship gates) + row_gate FINAL-bin C3 skip: rating

M10, 2026-11-25 ~07:45 (request 13:42Z). Read-only review. I did not run final_gate, because it writes into `build/agent12/session3/final/tmp`. I read M12's selftest and negative-control outputs instead.

## Files rated

| file | sha256/16 | bytes |
|---|---|---|
| build/agent12/session3/final_gate.py | 4C3F0DC113167E74 | 19705 |
| build/agent12/session3/FINAL-F-GATES.md | E57976239C1C50AA | 4892 |
| build/agent12/session3/final/selftest.txt | C697E2371BCA18BC | 447 |
| build/agent12/session3/row_gate.py | E290FD8053A104DE | 7604 |
| build/agent12/session3/row_gate.py.pre-final (base) | 7E4531124779B387 | 7033 |

Base:
- final-defaults-rating.md (C20B6FDB), section "Functional set" F1-F7 and N1;
- final-build-rating.md (94CC9FA7);
- check-defaults.py D9936C56.

## Verdict

**SAFE-IF**, conditions G1-G4.
- The tool covers every item of my F1-F7 set, and on most of them it is stricter than the spec.
- Exit codes are 0 PASS / 1 FAIL / 4 HOLD / 2 usage. Precedence is FAIL > HOLD > PASS. An uncaught exception exits 1, so it fails closed.
- The row_gate skip can't hide a problem on a non-final bin.

## What I checked

**Coverage against my functional set**
- **F1:**
  - checks: cvars exactly `{framerate_limit=0}` (harness `cvars`, or matrix `params.cvar` + `toml_set`); no `LEGO_GPU_WAIT_*`; `check-defaults --mode xenos` PASS, which includes the full S1 back-off line; clean exit; bin id.
  - The F1 route itself (WC light) isn't checked. See N2.
- **F2:**
  - `C1 keep-watch: on (with …)` exactly once.
  - 10 bad strings, a superset of check-defaults' 5 that includes the stale-recovery string.
  - elapsed ≥ 590 s, a `level` script, the vortex mark, steps n/n with 0 timeouts, Toypad lines > 0.
  - xenos mode is a NOTE (see S2).
- **F3:** exactly the 12 old values from cvars, env `LEGO_GPU_WAIT_BACKOFF_US=off` (lowercase), and `--mode off` PASS.
- **F4:**
  - env `LEGO_GPU_WAIT_*` == `{BACKOFF_US=500}`, plus xenos PASS.
  - The optional `--pair` check compares the proof lines with F1's, with only the source tag normalised.
- **F5:**
  - native-old PASS.
  - The run-dir exe has 1616… and not 9b40…, and native-gpu-build.txt reads exactly `LEGO Dimensions native GPU 1616ce65e973c583`.
  - The nativefinal MANIFEST lists A33801D1 + E3CB99CF, and the run-dir DLLs equal the BIN-PINS table.
  - Miss warnings are ≤ the `--ref` n0 run, per class and in total.
  - With no ref the result is HOLD. The ref 0400-n0-r1 is fine: all 15 W8a runs give the same 2/8/8/8.
- **F5w (my "2nd launch loads the recipes"):**
  - The `--first` run must have saved ≥ 1 recipe.
  - This run needs `loaded ≥ 1, failed=0`, with 0 "no startup pipeline recipes yet" lines and 0 "ignoring invalid" lines.
  - failed=0 is a good addition.
- **F6:** the `OFF (LEGO_NATIVE_SHADER_MISS_CACHE set)` line exactly once, the ON line 0 times, and no native-old FAIL other than the ON-line count.
- **F7:**
  - clean, plus the F2 route items except C1.
  - The HOLD applies only when check-defaults exits 1 and **every** FAIL is `miss cache ON (build default) line: 0`. Any bad string or any other line makes it FAIL. This is the correct form of my N1.

**Common checks**
- run.json exit 0, not early, no WER/dialogs/crash events, no dumps (dir glob plus run.json), WM_CLOSE, and `Title terminated` x1.
- Bin identity:
  - `bin_dir` basename equals the row's bin;
  - the bin MANIFEST sha equals BIN-PINS;
  - the run-dir MANIFEST copy, the exe and both DLLs equal the pins.
- check-defaults is pinned to D9936C56 (sha checked on every call).

**Joined, rotated logs**
- `log_files` orders `game.N.log` from highest N (oldest) to `game.1.log`, then `game.log`. That is the spdlog rotating order, and the selftest covers it.
- Joining is the right input for check-defaults: its "exactly once" semantics are per launch, and a rotated launch spreads its proof lines (startup, in game.1.log) across files.
- The joined copy is rewritten on each call, before check-defaults reads it.
- This holds only while a run dir holds exactly one launch (G1).

**row_gate change**
- The diff is limited to C3. The keep-watch, back-off, host-timer and precise-wait "line iff cvar/env set" checks are skipped only when the run.json `bin_dir` basename is one of the 4 FINAL bins, and a NOTE then points to final_gate.
- `C1 verify: on.` iff verify, the split check, C4, C5, C6 and the rest stay active on every bin.
- Non-final bins: M12's before/after outputs for s33offsf and s4b07f have identical lines (the files differ only in bytes, not in any line).
- A run that falsely claims a FINAL `bin_dir` still has to pass final_gate's MANIFEST, exe and DLL pin checks, so it can't slip through (G2).

**Negative controls (selftest 12/12, `neg-win3-F1.txt`)**
- win3 (devoff4b) as F1 FAILs on: bin_dir, the MANIFEST copy, exe/DLL pins, cvars, env, and check-defaults xenos (15 FAILs, including "Final defaults lines: 0").
- The common checks all PASS on that real old-bin run, so the bad-string list and `Title terminated` don't false-FAIL on a normal run.
- native4b n0 as F5 FAILs on the bin and on native-old.

## Conditions

- **G1:** each F run dir holds exactly one launch.
  - F5w is a separate run dir that reuses F5's `cache/` (M3's draft must say how). Its `game*.log` must not contain the first launch.
  - Otherwise the joined log double-counts and the check FAILs falsely (closed), or, worse, F5w could read the 1st launch's lines.
- **G2:** on FINAL bins, a row_gate result alone is never a gate. Every FINAL-bin run used for F1-F7 or any confirmation needs final_gate PASS (or a ruled HOLD) as well. State this in M3's draft.
- **G3:** there is no positive control yet, because no FINAL-bin runs exist. For the first F1 and the first F5 PASS, send me (or the Overseer) the full final_gate output with every line, so the PASS lines can be eyeballed once before the rest of the rows are trusted.
- **G4:** a HOLD (exit 4) stops the chain until the Overseer rules.
  - For F7's miss-cache HOLD, the ruling must cite the run's miss-warning count, which must be 0 (S1).
  - For F5 without `--ref`, rerun with `--ref`. Don't rule it through.

## Findings

- **SHOULD S1 (F7, and F5w):** make the N1 HOLD automatic.
  - If the miss-cache ON line is absent and `miss_counts` total == 0, the result is HOLD (or PASS-with-NOTE). If the line is absent and the total is > 0, the result is FAIL: misses happened and the cache didn't report, which is a real defect.
  - Apply the same rule to F5w. On a warm second launch, the first-miss line may not appear if the warm path avoids the miss path, and F5w has no HOLD branch today, so it would FAIL falsely (closed).
- **SHOULD S2 (F2):** raise xenos-not-PASS from NOTE to HOLD when F2's switch checks pass (no SDK key, no back-off env).
  - In that case xenos should PASS exactly as on F1. A failure would point to a real startup anomaly (doubled lines, a missing dump line) that the route checks don't see.
- **SHOULD S3 (OFF bins):** row_gate skips C3 on `devfinal-off-bin` and `nativefinal-off-bin`, but final_gate has no row for them (ROW_BIN covers only devfinal and nativefinal).
  - A run on an OFF bin would therefore get no init-line check at all.
  - Before any OFF-bin run is used, add a row with its own mode. Option: devfinal-off = xenos minus the back-off line plus `GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=` once. The other option: say that OFF-bin runs aren't gated and aren't used.
- **NIT N1:** 590 s stands in for "≥ 10 min", which is 1.7 % lenient. That's acceptable for a route timed at about 600 s. Record the actual elapsed time in the report.
- **NIT N2:** F1 doesn't check the route name (WC light). Add an `input_script` check like F2's, or rely on M3's queue.
- **NIT N3:** the bin_dir match is by basename only. The pin checks make this safe.
- **NIT N4:** unknown `--options` are ignored silently. A typo in `--ref` gives HOLD, and a typo in `--first` gives FAIL, so both fail closed.
- **NIT N5:** the joined-log temp name is the run dir's basename, so two concurrent gates on same-named runs from different matrices would collide. Gate one run at a time, or add the parent dir to the name.
- **NIT N6:** F5w could also require loaded == the first launch's saved N (exact reuse). It currently requires only ≥ 1.

## Read / Sent

- **Read:**
  - final_gate.py in full;
  - FINAL-F-GATES.md;
  - selftest.txt;
  - neg-win3-F1.txt;
  - the row_gate diff (pre-final → current);
  - rg-s33offsf / rg-s4b07f before/after (line compare);
  - final-defaults-rating N1 (miss-cache line logged on the first miss).
- **Sent:** the verdict and sha8 to the Overseer.

## v2 conformance (M10, 07:53): CONFORMS

| file | sha256 (16) |
|---|---|
| final_gate.py v2 | 9DCC72EEEEEEB5F4 (30755 B) |
| final_gate-v2.diff | C304214CDF8403DE |
| FINAL-F-GATES.md v2 | 9F7A33E6CD7C3174 |
| final/selftest.txt | 014709329B8D5E95 (SELFTEST 35/35, 0 BAD) |
| final/neg-win3-F1.txt | BC53526C7559C44A (F-GATE F1 0319-win3-r1: FAIL) |

- Diff: final_gate-v2.diff applied (LF, headers rewritten) to the v1 backup 4C3F0DC1 in my scratch gives exactly 9DCC72EEEEEEB5F4. Nothing outside the diff changed.
- `_selftest_nobin`: a default-False parameter of gate(). main() calls gate() with ref/first/pair only (options go into a dict, no `**opts`), so the CLI can't reach it. When it's set, it skips only the run-dir exe/DLL hashes and the exe fingerprint scan, each recorded as NOTE "skipped (selftest)". Bin_dir, MANIFEST vs BIN-PINS, exe_sha256 vs pin, native-gpu-build.txt, the MANIFEST DLL ids and check-defaults (hash-pinned D9936C56) still run. Without the flag, a missing run-dir file is a FAIL.
- S1: the gate is automatic.
  - F7/F5w: HOLD only when check-defaults exits 1 and every FAIL is the absent ON line and the shader-miss count is 0. With >0 misses it's FAIL; any other FAIL or exit code takes the normal FAIL path.
  - F6: no miss-cache line at all + 0 misses → HOLD, >0 → FAIL. Otherwise it needs exactly 1 expected OFF line, 0 ON lines and 1 line of any kind.
- S2: an F2 xenos not-PASS is HOLD only when the switches are clean (no SDK key, no LEGO_GPU_WAIT_*). Otherwise it's a NOTE, and the switch FAILs above already make the verdict FAIL. FAIL always beats HOLD in verdict().
- S3: ROW_BIN has F3 = devfinal-off-bin (mode off, 12 old values plus back-off env off) and F6 = nativefinal-off-bin (env unset → "OFF (build default)", env 0 → the env OFF line). natoff keeps fingerprint 1616ce65e973c583 (BUILD-STEPS L189), so the F6 fingerprint check is correct. The real negative controls cover both: win3 as F3 and n0 as F6 both FAIL.
- N1: elapsed is a NOTE on every row (source elapsed_s or end-start); the F2/F7 590 s floor uses it. N5: tmp name = parent__run__sha8(normcase abspath), unit-tested. N6: loaded-vs-saved is a NOTE only.
- Selftest writes only under build/agent12/session3/final/tmp (selftest-fx, selftest-rot and the joined logs). That's 35 tests: 19 synthetic fixtures plus 5 real negative controls, all of which FAIL closed.
- G1-G4 stand as before. With S1/S2 automatic, an F7/F5w/F6 HOLD ruling still has to cite the 0-miss count shown in the HOLD line.
