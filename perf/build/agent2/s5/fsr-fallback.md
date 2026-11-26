# FSR fallback: Xenos presenter and native path (Task 1.1)

Read-only research. Sources:
- SDK = `DimensionsRecomp/rexglue-sdk` @ `a7e79c0` (working tree HEAD verified).
- Superproject = `DimensionsRecomp` @ `a8e8dc8` (verified; same code as 2de88ce).
- Paths below are commit-relative unless they are prefixed `WS\`.

## (a) Xenos path: present_effect=fsr/cas without FidelityFX

### Where the define comes from
- `src/ui/CMakeLists.txt:122-128` (SDK): `REX_HAS_FIDELITYFX_SDK=1` is added as a **PRIVATE** compile definition of `rexui`. It is set only when `REXGLUE_FIDELITYFX_SOURCE_DIR` is set and `${REXGLUE_FIDELITYFX_SOURCE_DIR}/sdk/include` exists.
- `src/ui/CMakeLists.txt:130-141`: `REX_HAS_FIDELITYFX_RUNTIME` is set only if the `amd_fidelityfx_dx12` or `amd_fidelityfx_vk` targets exist. Those targets come from `cmake/rexglue_fidelityfx.cmake`, which returns immediately when `REXGLUE_ENABLE_FIDELITYFX` is OFF (`:7-9`).

### Is it defined in snap1-sdk? **No.**
- `WS\build\agent2\snap1-sdk\CMakeCache.txt:441`: `REXGLUE_ENABLE_FIDELITYFX:BOOL=OFF`. The cache has no `REXGLUE_FIDELITYFX_SOURCE_DIR` entry at all.
- `WS\build\agent2\snap1-sdk\compile_commands.json`: 2277 entries (759 per config × Debug/Release/RelWithDebInfo). **None of them contains the string `FIDELITYFX`.**
- The full define set for the presenter TU (`src/ui/presenter.cpp`, Release) is:
  `-DNOMINMAX -DREXGLUE_BUILD_CONFIG="Release" -DREXGLUE_ENABLE_PERF_COUNTERS -DREX_HAS_D3D12=1 -DREX_PLATFORM_WINDOWS=1 -DSPDLOG_COMPILED_LIB -DSPDLOG_FMT_EXTERNAL -DWIN32_LEAN_AND_MEAN -DCMAKE_INTDIR="Release" -DNDEBUG -D_DLL -D_MT`

### Code path when the define is off
1. **Cvar registration**, `src/ui/presenter.cpp:43-78`.
   - With the define (`:43-73`), it registers `present_effect` with allowed values `{bilinear, cas, fsr, fsr2, fsr3}`. It also registers `present_cas_additional_sharpness`, `present_fsr_max_upsampling_passes`, `present_fsr_sharpness_reduction` and `present_fsr_quality_mode`.
   - In the `#else` branch (`:74-78`), only `present_effect` is registered: default `"bilinear"`, `.allowed({"bilinear"})`, kRequiresRestart. **No `present_fsr_*` or `present_cas_*` cvar exists.**
2. **Enum**, `include/rex/ui/presenter.h:213-229`. Without the define, `Effect` has only `kBilinear`. The FFX members (`:276-302`, `:317-322`) and the extra GuestOutputPaintEffect values (`:427-441`, `:473-480`) are compiled out.
3. **Parsing**, `src/ui/presenter.cpp:101-120`. `ParsePresentEffect` compiles its cas/fsr/fsr2/fsr3 branches only under the define (`:105-118`). Otherwise it always reaches `return Effect::kBilinear;` (`:119`). Nothing is logged.
4. **Applying**, `src/ui/presenter.cpp:264-283`. `BuildGuestOutputPaintConfigFromCVar` calls `config.SetEffect(parsed_effect)` (`:273`). The only log in this area is the fsr2/fsr3 "temporal not available" warning (`:245-252`, `:267-271`), and that is inside `#if defined(REX_HAS_FIDELITYFX_SDK)` too.

### Is the cvar value still accepted? It depends on where the value comes from (`src/core/cvar.cpp`)
- **TOML (legodimensions.toml): rejected.** The path is `ApplyTomlTable` (`:97-138`) → `SetFlagFromSource` (`:298-327`) → `ValidateConstraints` (`:160-212`).
  - `'fsr'` is not in `{"bilinear"}`, so it logs `REXLOG_WARN "Flag '{}': '{}' not in allowed values"` (`:200`) and then `"Config: invalid value for cvar '{}'"` (`:133`).
  - The value stays `"bilinear"`.
  - The unregistered `present_fsr_*` TOML keys are deferred (`:118-122`). `FinalizeInit` then logs `"Config: unknown cvar"` (`:719-727`).
- **Command line or environment: accepted without validation.** `ApplyFromSource` (`:87-94`) is commented "Unvalidated apply, for the command line and environment paths". It is used by `Init` (`:622-677`, calls at `:631`, `:637`) and by `ApplyEnvironment` (`:694-717`; env var name `REX_PRESENT_EFFECT` via `FlagNameToEnvVar` `:70-77`).
  - So `--present_effect=fsr` stores `"fsr"` with no warning.
  - `ParsePresentEffect` then silently returns bilinear.
- **Runtime `SetFlagByName`: validated.** It goes through `Source::kRuntime` (`:342-344`). This is the path the native overlay menu and the app's fsr2/fsr3→fsr remap use (see (b)), so those are rejected the same way as TOML.

### Is anything logged? Not to game.log.
- `src/ui/rex_app.cpp:224` and `:277` load the config **before** `rex::InitLogging(log_config)` runs at `:293`.
- Before InitLogging, the only sink is an msvc_sink, i.e. OutputDebugString (`src/core/logging.cpp:167-197`, sink at `:173`). It is removed at `:236-241` and nothing is replayed.
- So the two TOML-rejection warnings above go only to an attached debugger. They never reach `game.log` (confirmed in (c)).
- The format string `': '{}' not in allowed values` does exist in `WS\build\agent2\nativefinal2-bin\rexruntime.dll`, but none of the logs contain it.

## (b) Native path: why `spatial_fsr_presented=0`

### Where it is counted (superproject `rexlego/src/gpu_native/device.cpp`)
- `:2048`:
  `fsr1_requested = !NativeFsr3Enabled() && (settings ? settings->fsr1 : rex::cvar::GetFlagByName("present_effect") == "fsr")`
- `:2061-2080`: if requested, it runs `Fsr1Presenter::Draw`. On failure it logs `"Native FSR 1: presentation setup failed; using the native spatial copy"`, at most 8 times (`:2074-2076`).
- `:2081`: otherwise, the plain spatial copy.
- The metrics are written at `:2219` (`u64(spatial_presented)`) and `:2265`, with the CSV header at `:2316` and the row write at `:2347`.

### Conditions and defaults
- `rexlego/src/gpu_native/settings_snapshot.cpp:69-71`: `snapshot.fsr1 = (present_effect == "fsr")`. Defaults are in `settings_snapshot.h:25,29,30` (fsr1=false, passes 4, sharpness 0.2f).
- `rexlego/src/gpu_native/settings_registry.cpp`:
  - effects list `{"bilinear","fsr"}` (`:25`)
  - catalog `native_fsr3` default `"true"` (`:35`)
  - `present_effect` default `"bilinear"` (`:40`)
  - FSR1 cvars (`:41-42`)
  - an unregistered cvar reads its catalog default (`:104-106`, the fix-a behaviour)
- Inputs that set FSR1:
  - `native_overlay.cpp:121`: the in-game menu calls `SetFlagByName("present_effect", selected==1 ? "fsr" : "bilinear")`. This is validated, so it is **rejected** under the non-FFX SDK.
  - `legodimensions_app.h:440-450`: `OnPostInitLogging` remaps fsr2/fsr3 → fsr through `SetFlagByName`. Also validated, so also rejected.
- FSR1 needs no FFX DLL. `rexlego/src/gpu_native/fsr1_present.h:16-19` includes the SDK's precompiled bytecode headers (`src/ui/shaders/bytecode/d3d12_5_1/guest_output_ffx_fsr_easu_ps.h` and the RCAS one). The only thing missing is that `present_effect=="fsr"` gets accepted.
- So FSR1 runs only when:
  - `native_fsr3` is false, **and**
  - the `present_effect` cvar actually holds `"fsr"`.
- In the shipped SDK build, `present_effect` can only hold `"fsr"` if it was set through the unvalidated command-line or env path.

### Is nativefinal2's `amd_fidelityfx_dx12.dll` loaded? **No. It is copied but never used.**
- `rexlego/CMakeLists.txt:256-274`:
  - includes `rexglue-sdk/thirdparty/FidelityFX-SDK/sdk/include`
  - links the **static** libs `rexglue-sdk/bin/ffx_sdk/ffx_backend_dx12_x64.lib` + `ffx_fsr3upscaler_x64.lib`
  - `find_file(LEGO_NATIVE_FIDELITYFX_RUNTIME amd_fidelityfx_dx12.dll …)` fails the configure (FATAL) if the DLL is missing (`:264-270`)
  - the DLL is only copied next to the exe as a POST_BUILD step (`:271-274`)
- `fsr3_upscaler.cpp:11-12,98-185` uses the FFX 1.1 host API (`ffxGetInterfaceDX12`, `ffxFsr3UpscalerContextCreate`), not ffx-api, so nothing needs `amd_fidelityfx_dx12.dll`.
- PE import check (own parser, since pefile is not installed) on `WS\build\agent2\nativefinal2-bin\`:
  - `legodimensions.exe` imports rexruntime, d3d12, dxgi, KERNEL32, USER32, WINMM, ole32, SHELL32, MSVCP140(+_ATOMIC_WAIT), VCRUNTIME140(_1) and api-ms-win-crt-*.
  - It has **no delay-import directory**.
  - It contains **no "amd_fidelityfx" string**, in either ASCII or UTF-16, so there is no LoadLibrary-by-name either. `rexruntime.dll` and `rexgpu-xenos.dll` are the same.
- `legodimensions.map:334197-334204` shows `ffxGetScratchMemorySizeDX12` / `ffxGetInterfaceDX12` resolved from `ffx_backend_dx12_x64:ffx_dx12.cpp.obj`. That means static linking.
- The DLL itself is 6,675,664 B, SHA-256 prefix 12A5081257EC95B0. It is AMD's prebuilt signed DLL from `thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/`.

## (c) Evidence from existing logs

### Runs examined
- `WS\build\agent8\session3\smoke-final2\runs\20261125-164755-final2-3d-xenos\game.log`
- `WS\build\agent8\session3\smoke-final2\runs\20261125-165219-final2-3d-native\game.log`
- `WS\build\agent8\runs\1613-devfinal2-smoke\game.log`
- `WS\build\agent8\runs\1618-nativefinal2-smoke\game.log`

### Grep results
Pattern: `present_effect|fsr|FSR|cas|FidelityFX|spatial|upscal|presenter|resolution scale|allowed values|invalid value|unknown|Config`. The only hits:

| File:line | Line |
|---|---|
| …164755-final2-3d-xenos\game.log:14 | `Startup: presenter attached to the window` |
| 1613-devfinal2-smoke\game.log:14 | `Startup: presenter attached to the window` |
| …165219-final2-3d-native\game.log:23 | `Native GPU capabilities: … fsr3_capable=true` |
| 1618-nativefinal2-smoke\game.log:25 | `Native GPU capabilities: … fsr3_capable=true` |

None of the logs contains a `not in allowed values`, `invalid value`, `unknown cvar` or `Native FSR 1:` line.

### What the runs asked for
- Every run's `legodimensions.toml` has:
  - `:37 present_effect = 'fsr'`
  - `:38` max_upsampling_passes 1
  - `:39` quality_mode 'quality'
  - `:40` sharpness_reduction 0.0
  - `:41 present_dither = true`
  - `:49 resolution_scale = 1`
  - `:72 native_settings_frontend = true`
  - `:73 native_fsr3 = false`
- The `run.json` args (`1613`/`1618` run.json `:5-10`) are `--log_file`, `--perf_log_csv`, `--native_settings_load=false`, `--discord_rpc=false`, `--audio_mute=true`, `--pause_when_unfocused=false`.
  - There is no `--present_effect` argument.
  - There is no `REX_PRESENT_EFFECT` env var. The session3 run.json env has only `LEGO_NATIVE_FRAME_METRICS` (`:16`).

### Native frames
- The session3 native `frames.csv` has 36193 rows, with max `spatial_fsr_presented=0` and max `fsr_enabled=0`.
- The last row: output 2240x1294, scene 1920x1080, present_source 1920x1080.
- Earlier notes agree: `WS\perf\build\agent7\n-rows\native-summary.txt:9` "spatial_fsr_presented=0 fsr_enabled=0".

## Verdicts
- **silent fallback: yes**, because the shipped SDK (snap1-sdk) is built without `REX_HAS_FIDELITYFX_SDK` (`CMakeCache.txt:441` OFF, and 0 FIDELITYFX defines in compile_commands).
  - `Presenter::Effect` then has only `kBilinear` (`presenter.h:213-229`), and `ParsePresentEffect` returns bilinear for anything (`presenter.cpp:119`).
  - A TOML `'fsr'`/`'cas'` is rejected by `.allowed({"bilinear"})` (`presenter.cpp:74-78`, `cvar.cpp:200,133`). The warning goes only to the pre-InitLogging debugger sink (`rex_app.cpp:224/277` vs `:293`, `logging.cpp:173`), not to game.log.
  - A command-line or env `fsr` is stored unvalidated (`cvar.cpp:87-94`) and then parsed to bilinear with no log at all.
- **spatial_fsr_presented=0 because** FSR1 is never requested, not because it failed.
  - The runs set `native_fsr3=false` (so the native path *would* do FSR1). But the `present_effect` cvar stays `"bilinear"`, because the TOML `'fsr'` is rejected by the non-FFX SDK's allowed list. So `fsr1_requested` at `device.cpp:2048` is false.
  - The fallback copy at `:2081` runs, and there is no "Native FSR 1: presentation setup failed" line in any log.
  - The `amd_fidelityfx_dx12.dll` shipped with nativefinal2 plays no part. It is POST_BUILD-copied only (`rexlego/CMakeLists.txt:271-274`). It is neither imported nor delay-loaded, and FSR3 is statically linked.
