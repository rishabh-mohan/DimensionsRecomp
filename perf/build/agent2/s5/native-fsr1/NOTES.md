# S5 item 4: native accepts present_effect=fsr on a non-FidelityFX SDK (staged, NOT built, NOT applied)

- Base: rexglue-sdk a7e79c0. Diff: `native-fsr1.diff` (+35/-2, 1 file: src/ui/presenter.cpp).
- Verification: `check.py` → `check.txt` (RESULT: PASS). The 4 compiler warnings are all pre-existing. check.py recompiles the unmodified TU and compares them.

## Problem
- snap1-sdk is built without `REX_HAS_FIDELITYFX_SDK`. So presenter.cpp:74-78 (the a7e79c0 `#else`) registers `present_effect` with `.allowed({"bilinear"})`, and registers no `present_fsr_*` cvars at all.
- The native renderer has its own FSR 1 (EASU/RCAS from precompiled bytecode). It gates on `present_effect == "fsr"`:
  - rexlego/src/gpu_native/device.cpp:2048 (`fsr1_requested`)
  - settings_snapshot.cpp:69
- It reads `present_fsr_sharpness_reduction` and `present_fsr_max_upsampling_passes`:
  - device.cpp:2064/2066
  - settings_snapshot.cpp:70-71
- Because the TOML value 'fsr' is rejected, native never runs FSR 1, and the log shows `spatial_fsr_presented=0` (see fsr-fallback.md).

## Design (only the `#else` branch changes; the FFX branch is byte-identical)
1. `present_effect` (#else): `.allowed({"bilinear", "fsr"})`, with a new description and a comment. The default stays "bilinear".
2. The same `#else` also defines the two cvars that native reads, with the FFX build's defaults and ranges. Literals are needed because presenter.h:254-260 constants exist only under the define:
   - `present_fsr_max_upsampling_passes`: INT32, default 4, range 1-4, kRequiresRestart.
   - `present_fsr_sharpness_reduction`: DOUBLE, default 0.2f, range 0-2, kRequiresRestart.
   - rexlego's flags.h:21-25 already declares both unconditionally as int32_t/double, so these definitions match.
   - The native catalog (settings_registry.cpp:40-42) uses the same defaults (bilinear / 0.2 / 4) and ranges.
3. A one-time INFO log under `#else`, `LogBilinearFallbackOnce()` (overlay :281-290), is called from `BuildGuestOutputPaintConfigFromCVar` (overlay :299-302) when the value is not "bilinear". It logs: `present_effect=fsr: this build has no FidelityFX SDK, so the SDK presenter uses bilinear (a GPU path with its own FSR 1 still applies it)`.
   - The function runs once, at `Presenter::InitializeCommonSurfaceIndependent` (overlay :820), which is after InitLogging, so the line lands in game.log.
- `present_cas_additional_sharpness` and `present_fsr_quality_mode` were not added. Native doesn't read them, and the Xenos "cas" stays rejected.

## Why the Xenos side stays safe
- Without the define, `GuestOutputPaintConfig::Effect` contains only `kBilinear` (presenter.h:213-229).
- `ParsePresentEffect` returns `kBilinear` for anything other than the FFX names, which are compiled out (presenter.cpp:120-139 overlay / 101-120 base).
- No FFX code path exists in this TU to reach: every kCas/kFsr/kFsr2/kFsr3 user is under `#if defined(REX_HAS_FIDELITYFX_SDK)`.
- The only SDK reader of `present_effect` is `BuildGuestOutputPaintConfigFromCVar` (base :266).
- Result: Xenos with "fsr" presents bilinear exactly as today with "bilinear", plus one INFO line.
- The new `present_fsr_*` cvars are read nowhere in the SDK when the define is off, so they have no Xenos effect.

## Native side effects (rexlego at a8e8dc8, all via validated SetFlagByName/Query, which now succeed)
- device.cpp:2048: `fsr1_requested` turns on when `native_fsr3` is off and present_effect=fsr. As a result:
  - EASU/RCAS run.
  - `spatial_fsr_presented` should become 1.
  - device.cpp:2058 forces a clear while FSR1 is requested.
- native_overlay.cpp:116-121/141-143 and the frontend writers (settings_frontend.cpp:141, 231-234) can now select fsr and set sharpness.
- legodimensions_app.h:446-449: the fsr2/fsr3 → fsr remap succeeds instead of being rejected.
- settings_registry fallback `ReadRegistryValues` (:104-106) is no longer taken for the present_fsr_* keys. The save patch (:203) now writes them.

## Risks
- **Behaviour change in benches:** tomls that already contain `present_effect="fsr"` now really run FSR 1, which costs GPU time and changes frame timing. Bench tomls with `present_fsr_max_upsampling_passes=1` or `present_fsr_sharpness_reduction=0.0` now take effect (they differ from the catalog defaults 4 / 0.2). Re-baseline any perf comparison.
- **Xenos-only builds** accept 'fsr' but present bilinear. This is mitigated by the INFO line. The Xenos menu (ui_theme.cpp:182-186) still offers "cas", which stays rejected (unchanged).
- **Bench tooling:** perf/bench/agent7/native3_boot_check.py:340-347 treats the presence of the `present_fsr_sharpness_reduction` string in rexruntime.dll as "built with the FFX SDK" and would WARN or misreport. Update its heuristic, e.g. key on `present_fsr_quality_mode` or an `ffx` symbol instead.
- **Behaviour change in exe:** The crash/abort class "Native setting is not registered" for present_fsr_* goes away. That is intended, but it changes behaviour.
- **Restart:** The kRequiresRestart semantics are unchanged. The in-game toggle still needs a restart for the presenter, while native reads the cvar per frame / per snapshot as today.
- **Formatting:** The default 0.2f vs 0.2 serialises as "0.200000" either way (std::to_string), so a saved config is unchanged.
- **Build define:** If the SDK is later built WITH FidelityFX, the diff has no effect, because the FFX branch is untouched. Native and SDK FSR 1 would then both be selectable. That interaction is the same as today's FFX build.
- **Combining with item 3:** With toml-reject applied but without this diff, `present_effect='fsr'` gets logged as rejected. With both applied, it is accepted and the INFO line is logged instead.

## PCH / rebuild scope
- Headers changed: none (presenter.h untouched).
- Rebuild: 1 rexui TU (src/ui/presenter.cpp) using the existing rexui PCH (`cmake_pch.hxx.pch`, unchanged), then a rexruntime.dll relink. No game-exe rebuild is needed. The game reads the cvars by name, and flags.h already declares them.
- Single-TU compile from check.txt: about 1.2 s with the PCH.
