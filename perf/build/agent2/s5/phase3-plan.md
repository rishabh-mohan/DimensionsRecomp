# S5 Phase 3 test-bin plan: nops / toml-reject / native-fsr1 (M2, static draft)

## Recommendation: separate bins, one per diff. Combine only for a final promotion check.
1. **Incompatible gates.** toml-reject's T2 expects exactly one `present_effect='fsr' rejected` line.
   With native-fsr1 applied, 'fsr' is accepted, so T2 can never pass on a combined bin (native-fsr1 NOTES, "Combining with item 3").
2. **Different targets and legs.** nops/zpd-log = gpu-leg TUs, Xenos timing. toml-reject = rexcore (cvar.cpp, logging.cpp), log-only.
   native-fsr1 = rexui presenter.cpp. Its only real effect is on the **native** exe (FSR1 really runs: F1), so it changes native timing.
3. **Attribution.** If a combined bin regresses (crash, timing, visual), M10 would have to bisect anyway.
   Separate bins each reuse the proven devs5sync method: final2 base, only the diff's TUs recompiled, BASE gate reproduces the final2 obj,
   pe-check exports NEW==REF (toml-reject: plus the one additive `FlushDeferredConfigWarnings` export), MANIFEST, pinned bins untouched.
4. **Cost is small.** Each build is 1-2 TUs plus a rexruntime.dll relink (minutes). T1-T2 and F3 are short boot smokes, not timed windows.

## Bins (in order)
| # | bin dir (A2/s5/) | base | TUs | gates |
|---|---|---|---|---|
| 1 | devs5nops-bin | devfinal2 | pipeline_cache.cpp (stacked on sync-log), + d3d12/command_processor.cpp if zpd-log is rated | N1-N4, S1 (tonight, after the window) |
| 2 | devs5toml-bin | devfinal2 | src/core/cvar.cpp, src/core/logging.cpp | T1-T2 |
| 3 | natives5fsr1-bin | nativefinal2 | src/ui/presenter.cpp | F1-F3 |
| 4 | (optional) promotion bin | final2 | all of the above that passed | one no-regression smoke; T2 expectation becomes the native-fsr1 INFO line |

- Bin 2 is Xenos dev only. toml-reject is identical for native, so one bin is enough to prove the log path.
- Bin 3 needs only the native bin: on Xenos, native-fsr1 is "accept 'fsr', present bilinear, plus one INFO line" (checked in bin 4 if made).

## Bin 2 smoke (T1-T2)
- New pins (T1), its own BIN-PINS.md; nothing stacked on nops.
- Boot to title with the harness toml (present_effect='fsr'), ~60 s, self-closing, waiter-launched.
- Pass: exactly one `Config: present_effect = 'fsr' ... rejected (allowed: bilinear); keeping 'bilinear' ... (reported before logging started)` line.
  No new ERROR vs a devfinal2 boot with the same toml (diff of ERROR lines).
- Extra: a negative arm with `-Cvar` of an out-of-range value to see the CLI/env "applied unvalidated" WARN (optional).

## Bin 3 smoke (F1-F3)
- **F2 first:** native3_boot_check.py:340-347 (DimensionsRecomp/perf/bench/agent7) treats the
  `present_fsr_sharpness_reduction` string in rexruntime.dll as "FFX SDK". With native-fsr1 that string is always there.
  Proposed fix: key the FFX verdict on `present_fsr_quality_mode` (native-fsr1 does not add it) or an ffx symbol, and treat
  sharpness/passes alone as "native FSR1 cvars". I'll stage it as a diff under A2/s5/native-fsr1/ (repo file not mine to write);
  first I'll check the strings against the ffx-a build.
- **F1:** timing arms use `present_effect=bilinear`. Options: a perf toml copy (A2/s5/native-fsr1/perf-bilinear.toml) passed with
  `run-game.ps1 -Toml`, or run-game's per-arm cvar override (`Set-Toml present_effect bilinear`, recorded in run.json cvars).
  I prefer the toml copy because its sha256 is pinned and visible. FSR1 is its own arm (present_effect='fsr'); it is never compared to S5 native timing.
- Arms: B (bilinear, timing) vs N-FSR1 (fsr, timing of FSR1 cost) vs nativefinal2 + bilinear toml (baseline, same toml sha).
- **F3:** a screenshot plus `spatial_fsr_presented=1` in the native stats line on the FSR1 arm, and 0 on the bilinear arms.
  Screenshots go to the user's visual review.

## Not tonight
Bins 2-3 are Phase 3. Tonight's order stays: (1) nops `check.py --compile`, (2) devs5nops-bin + kit dryrun on the Overseer's GO.
