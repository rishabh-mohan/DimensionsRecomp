# Agent 6: native-bin first-boot crash triage (static only)

Written 2026-11-21 ~23:40 by Agent 6. Static analysis only: no runs, no live-tree edits.

> **Status (2026-11-22 02:06, session 3):** fix-a + fix-a-commit are **applied** to the live game repo at Agent 1's GO:
> `settings_registry.cpp` A3733700 → 4EC71328, `settings_preferences.cpp` C78112AA → 9CBE6DBF. Details, checks and undo
> are in the last section.

Run: `build/agent8/runs/2315-native` (native-bin = S1 + p1 + p2, `LEGODIMENSIONS_NATIVE_GPU=ON`).
Symptom: unhandled C++ exception `0xE06D7363` on the UI thread (t86424), right after the log line
"Native write tracking ...", which is the last line of `HostDevice::Create`/`Init` (`rexlego/src/gpu_native/device.cpp:918`).

## Verdict (high confidence)

The throw is `std::runtime_error("Native setting is not registered: present_fsr_sharpness_reduction")`
from `ReadRegistryValues` (`rexlego/src/settings_registry.cpp:104`). It happens while `OnPreLaunchModule`
constructs `NativeSettingsRuntime` (`rexlego/src/legodimensions_app.h:155-157`). Two things combine:

1. The run toml (= `harness/legodimensions.toml` plus `user_data_root`) sets `native_settings_frontend = true`,
   one of the "NativeGPU 0.2.0 defaults" from `package_native.py`. Without it, the code default is `false`
   (`settings_native_hooks.cpp:16`, kInitOnly).
2. The native settings catalog lists `present_fsr_sharpness_reduction` and `present_fsr_max_upsampling_passes`.
   The SDK registers these two cvars only under `#if defined(REX_HAS_FIDELITYFX_SDK)`
   (`rexglue-sdk/src/ui/presenter.cpp:43-78`; the `#else` branch defines only `present_effect`, allowed `{"bilinear"}`).
   `snap1-sdk` was configured with `REXGLUE_ENABLE_FIDELITYFX=OFF` on purpose, the same as the baseline
   (Agent 1 16:48 (5); `perf-notes/agent2-baseline.md:218,431,437`). So `rexruntime.dll` never registers them.

**This is not an S1 regression.** Every callee is byte-identical in baseline, the snap1 snapshot and the live tree
(table below). The baseline and devoff builds are `NATIVE_GPU=OFF`, so they never compile this
`#ifdef LEGODIMENSIONS_NATIVE_GPU` path. native-bin is the first ON build this session.
**native2-bin (S2) uses the same FFX-OFF `rexruntime.dll`, so it will crash the same way.**

The shipped NativeGPU 0.2.0 build must use an FFX-enabled SDK, since its menu offers FSR 1.

## Throw chain

1. `legodimensions_app.h:155`: `rex::cvar::Query<bool>("native_settings_frontend")` returns true (from the toml).
   `Query` never throws; it returns false for a missing cvar.
2. `legodimensions_app.h:156` constructs `NativeSettingsRuntime`.
3. `settings_runtime.cpp:127-130` constructs `SettingsRevisionCoordinator(CaptureBackend(registry), ...)`.
4. The coordinator's `State` ctor (`settings_revision.cpp:25`) calls `registry.read()`, with no try/catch.
5. `CaptureBackend::read` (`settings_runtime.cpp:77`) calls `ReadRegistryValues` (`settings_registry.cpp:100-110`).
6. For each catalog key, `rex::cvar::GetFlagByName(key)` returns `""` when the key is unregistered
   (`rexglue-sdk/src/core/cvar.cpp:373-381`). Then `settings_registry.cpp:104` throws
   `"Native setting is not registered: " + key`. The first missing key in catalog order is `present_fsr_sharpness_reduction`.
7. `OnPreLaunchModule` has no try/catch, so the exception is unhandled (`0xE06D7363`).

Why nothing threw earlier: `LoadNativePreferences` (`settings_preferences.cpp:45-50`) returns early because the
harness passes `--native_settings_load=false`. So the read in step 4 is the first registry read of the boot.

## Catalog keys (NativeSettingsDefaults) vs cvars registered in native-bin

| Key | Registered by | In native-bin |
|---|---|---|
| `fullscreen` | SDK `ui/window.cpp:37` | yes |
| `native_fps_limit`, `native_vsync`, `native_show_fps`, `native_anisotropic_override` | `gpu_native/device.cpp:75-81` | yes |
| `native_fsr3`, `native_fsr3_quality`, `native_fsr3_sharpen`, `native_fsr3_sharpness`, `native_fsr3_mip_bias`, `native_resolution_scale` | `gpu_native/fsr3_settings.cpp:8-16` | yes |
| `native_bloom`, `native_cel_shading` | `native_effects.cpp:16-20` | yes |
| `depth_of_field` | `cheat_menu.cpp:321` (game.log line 16 "Depth of field off") | yes |
| `present_effect` | SDK `ui/presenter.cpp:75` (non-FFX branch, allowed `bilinear` only) | yes |
| `present_fsr_sharpness_reduction` | SDK `ui/presenter.cpp`, FFX branch only | **NO** |
| `present_fsr_max_upsampling_passes` | SDK `ui/presenter.cpp`, FFX branch only | **NO** |

All `ConfirmationKeys()` entries are catalog keys, so they are covered by the table.
Related: `native_settings_frontend` is at `settings_native_hooks.cpp:16`, `native_settings_load` at `settings_preferences.cpp:10`.

## Other throw sites between device.cpp:918 and the end of OnPreLaunchModule (checked; none is the trigger)

- `CaptureInputs`: `Query<bool>("present_dither")` never throws. A missing `skip_pixel_shaders`-style flag reads as `""`, which is tolerated.
- `Inputs()`: `.at()` and `std::stoi` are safe on the captured values.
- `Decode` (`settings_runtime.cpp:80-85`) throws if `DecodeNativeRenderSettings` (`settings_snapshot.cpp`) fails.
  It would also fail on a missing key ("Native settings snapshot is missing ..."), but it runs after the read, which throws first.
- The `QueuedSettings` and `Transaction` ctors only store the backend and don't read
  (`settings_service.cpp:20-24,74-77`; `settings_transaction.h:65-66`).
- `PublishNativeSettingsService` only takes a lock. `AssertOwner` passes because we are on the UI thread.

## Evidence

- `build/agent2/snap1-sdk/CMakeCache.txt`: `REXGLUE_ENABLE_FIDELITYFX:BOOL=OFF`, `REXGLUE_USE_D3D12=ON`, `REXGLUE_USE_VULKAN=OFF`.
- `REX_HAS_FIDELITYFX_SDK` is set only in `rexglue-sdk/src/ui/CMakeLists.txt:122-128`, when
  `REXGLUE_FIDELITYFX_SOURCE_DIR/sdk/include` exists. That variable is set only if `REXGLUE_ENABLE_FIDELITYFX` is ON,
  and the option defaults to OFF (`rexglue-sdk/CMakeLists.txt:23`).
- Strings in `build/agent2/native-bin/rexruntime.dll`:
  - present: `present_effect` (offset 8996191), `present_dither` (8996149), and the short description "Guest output effect: bilinear";
  - absent: `present_fsr_sharpness_reduction`, `present_fsr_max_upsampling_passes`, and "Guest output effect: bilinear, cas".
- `rexgpu-xenos.dll` has none of the `present_*` strings. It isn't loaded in native mode anyway.
- `legodimensions.map` (run dir): `FLAGS_present_effect_storage_` is imported from `rexruntime.dll`. There is **no**
  `FLAGS_present_fsr_*` symbol anywhere. The two key names occur only as string literals in `settings_registry.cpp.obj`
  (the catalog). The exe has one copy of the literal "Native setting is not registered: " (offset 0x11929578).
- **Decisive:** the WER dump `build/agent8/runs/2315-native/legodimensions.exe.93080.dmp` holds the built message
  `Native setting is not registered: present_fsr_sharpness_reduction` at file offset 0x1AAA270F (heap, not the exe
  image). That is the exception's `what()`. Searched with `build/agent6/crash-triage/find-strings.ps1`
  (output in `build/agent6/crash-triage/dmp1-strings.txt` and `exe-strings.txt`).

## Callee diff: baseline vs S1/S2 snapshot vs live (sha256 prefix)

| File | baseline | snap1 | live |
|---|---|---|---|
| `rexlego/src/legodimensions_app.h` | F2E868DE | F2E868DE | F2E868DE |
| `rexlego/src/settings_registry.cpp` | A3733700 | A3733700 | A3733700 |
| `rexlego/src/settings_registry.h` | 24C5F56E | 24C5F56E | 24C5F56E |
| `rexlego/src/settings_revision.cpp` | FD7BFFAA | FD7BFFAA | FD7BFFAA |
| `rexlego/src/settings_service.cpp` | 9A191B06 | 9A191B06 | 9A191B06 |
| `rexlego/src/settings_transaction.h` | DA4C9E8F | DA4C9E8F | DA4C9E8F |
| `rexlego/src/settings_preferences.cpp` | C78112AA | C78112AA | C78112AA |
| `rexlego/src/settings_native_hooks.cpp` | CDCF24AC | CDCF24AC | CDCF24AC |
| `rexlego/src/gpu_native/settings_runtime.cpp` | 99F42A0C | 99F42A0C | 99F42A0C |
| `rexlego/src/gpu_native/settings_snapshot.cpp` | CC81A8E7 | CC81A8E7 | CC81A8E7 |
| `rexlego/src/gpu_native/fsr3_settings.cpp` | 57AA09BC | 57AA09BC | 57AA09BC |
| `rexlego/src/native_effects.cpp` | 7C1F6B93 | 7C1F6B93 | 7C1F6B93 |
| `rexlego/src/cheat_menu.cpp` | 59C50744 | 3729B503 | 3729B503 |
| `rexglue-sdk/src/ui/presenter.cpp` | B8CBD2FE | B8CBD2FE | B8CBD2FE |
| `rexglue-sdk/src/ui/window.cpp` | 206E4222 | 206E4222 | 206E4222 |
| `rexglue-sdk/src/core/cvar.cpp` | 4434007C | 4434007C | 4434007C |
| `rexglue-sdk/src/ui/CMakeLists.txt` | 25F1CACF | 25F1CACF | 25F1CACF |

The only difference, `cheat_menu.cpp`, is an `ImGuiListClipper` change in the cheat dialog's scan-results list
(+15/-9 around line 197). It is not on the startup path; `depth_of_field` (line 321) is unchanged and registered.
S1's own patches (p1 `device.cpp`, p2 plume) are not on the throw path either: the throw happens after
`device.cpp:918` has logged, and in code that did not change.

## No-rebuild workaround

Pass `--native_settings_frontend=false` on the command line (the CLI outranks the toml), or set
`native_settings_frontend = false` in the run toml (e.g. Agent 8's `Write-RunToml -Set`/`-Cvar`).
`--no-native_settings_frontend` should also work.

Why this is enough:
- `NativeSettingsRuntime` is not constructed, so the throwing read at startup never runs.
- The `QueuedSettings` ctor doesn't read.
- `LoadNativePreferences` is skipped (`native_settings_load=false`), and even when it runs, its read sits inside try/catch.
- `Transaction::Open` reads only later, and inside try/catch.
- The renderer uses the legacy direct-cvar path: `AcquireNativeSettingsRuntime()` returns null at
  `device.cpp:1878`, `draw.cpp:5412` and `shaders.cpp:476`. That is the code default
  (`perf-notes/agent8-runtime-features.md:100`).

Caveat: this differs from the shipped 0.2.0 config (frontend on). The in-game menu falls back to the legacy F5 ImGui
native graphics menu. Rendering settings still come from the same cvars.

## Fixes for a later build (Fix A applied 11-22 02:05, see the last section; Fix B not applied)

**Fix A (smallest code fix).** In `ReadRegistryValues` (`rexlego/src/settings_registry.cpp:103-104`): when
`GetFlagByName` returns `""` and `rex::cvar::GetFlagInfo(spec.key) == nullptr`, use `spec.default_value` instead of throwing.
This keeps `Values` complete, so `Decode` still works. FSR 1 stays inert because `present_effect` only allows
`bilinear` without FFX.
- Also skip unregistered keys in `LoadNativePreferences` (treat them like overridden keys). Otherwise a saved
  FSR 1 value that differs from the default would make `SetFlagByName` fail, which leads to recovery_failed and Quit.
- Optional: hide the two rows through the `availability` callback, which is passed as `{}` at `legodimensions_app.h:128`.

**Fix B (build config).** Build the native SDK with `-DREXGLUE_ENABLE_FIDELITYFX=ON` (FetchContent from
github.com/rexglue/FidelityFX-SDK, or `FETCHCONTENT_SOURCE_DIR_FIDELITYFX` pointing at the initialised
`rexglue-sdk/thirdparty/FidelityFX-SDK` @eee08db). This is heavy, and `rexruntime.dll` is shared with the devoff
builds, so it changes OFF-build behaviour: the harness's `present_effect='fsr'` would start to take effect.
**Not recommended for the timing comparisons.**

## Fix A as a unified diff (text for the S3 proposal; applied with hunk 3 on 11-22 02:05, see the last section)

Agent 1 asked for this at 23:41, for Agent 7's S3 proposal and Agent 10's rating. No tree edits were made.

**Default behaviour is unchanged whenever every catalog key is registered.** That covers every FFX-ON SDK build,
including the shipped 0.2.0. In hunk 1 the new check runs only after `GetFlagByName` has returned `""`. In hunks 2
and 3, `GetFlagInfo` is the last operand of the existing `||` chain, so it costs one registry lookup per key that
would otherwise be applied or saved, and it returns non-null for every registered key. Only builds that lack a
catalog cvar behave differently, and those builds crash at startup today.

The files are under `build/agent6/fix-a/`. Paths in the patches are relative to `DimensionsRecomp/`, and content
lines are CRLF, like the targets.
- `fix-a.patch` (sha256 `71AEFF3DE46F2BC319E001FAE9F99EE6A3C0F48B4116F23B53CBEDF17C230424`): hunks 1 and 2, the requested fix.
- `fix-a-commit.patch` (sha256 `50046A3FE23DCF03C0CE65BE860308EF754ED361F462B6EE17588B5757A7374D`): optional hunk 3.
  It applies on top of fix-a or on its own.
- Full patched copies, for a hash-checked copy (Option A, as with S1+p1):

| File (under `DimensionsRecomp/`) | Before (live = snap1 = baseline) | After fix-a (`new/`) | After fix-a + hunk 3 (`new-commit/`) |
|---|---|---|---|
| `rexlego/src/settings_registry.cpp` | `A37337001EBDC277B2B94D783939A47096423F0AE8962C8B879A6A60B4F8BA4B` | `8BA19C5F9AC2090FD6921CE01A05EAA8AB648CD3718DF68EEAF8A372BE4A4DB5` | `4EC71328043FA6BA8C198D5AAFBFB7D0265CD1939ECE13D1CE11B6A7A48DB77D` |
| `rexlego/src/settings_preferences.cpp` | `C78112AA6E50F79D8E6154A37E47CC129C43EAD2E39EC066927374EFBF34B5F0` | `9CBE6DBF9CEDA62D61469235A828B84017340D356C166335BF53E9AB18565730` | same as fix-a |

### Hunk 1: `rexlego/src/settings_registry.cpp:103-104` (`ReadRegistryValues`)

A catalog key that is not registered (`GetFlagByName` returns `""` and `GetFlagInfo` returns null) now reads as
`spec.default_value` instead of throwing. `Values` stays complete, so `Decode` / `DecodeNativeRenderSettings` still
succeeds. A registered cvar whose value is empty still throws, as before. In native-bin this yields
`present_fsr_sharpness_reduction=0.2` and `present_fsr_max_upsampling_passes=4`, the catalog defaults (lines 41-42).

### Hunk 2: `rexlego/src/settings_preferences.cpp:69-71` (`LoadNativePreferences`)

A saved value for a key that is not registered is skipped like an override: it is listed in `result.overridden`
and never written. Hunk 2 is needed because of hunk 1. Today, `baseline = backend.read()` (line 67) throws first,
the catch only logs a warning, and nothing is written. With hunk 1 alone, the read succeeds. A
`native-settings.toml` saved by an FFX build with a non-default FSR 1 value then fails at `backend.write`, because
`SetFlagByName` returns false for an unknown cvar. The rollback of that key fails the same way, `recovery_failed`
is set, and `legodimensions_app.h:138-141` logs an error and calls `QuitFromUIThread()`. This only matters with
`native_settings_load=true`; the harness passes false.

### Hunk 3 (optional): `rexlego/src/settings_registry.cpp:200`, line 203 after fix-a (commit callback in `MakeNativeRegistryBackend`)

The commit patch skips keys that are not registered. A non-FFX build then never writes the two FSR 1 defaults into
`native-settings.toml`, where they would overwrite values saved by an FFX build. This follows the existing rule in
that loop, which already skips temporary overrides.

```diff
diff --git a/rexlego/src/settings_preferences.cpp b/rexlego/src/settings_preferences.cpp
--- a/rexlego/src/settings_preferences.cpp
+++ b/rexlego/src/settings_preferences.cpp
@@ -67,8 +67,10 @@ PreferencesResult LoadNativePreferences(const std::filesystem::path& path, Backe
     baseline = backend.read();  // Also enforces the backend's owning thread.
     for (const auto& [key, value] : proposal) {
       const auto source = rex::cvar::GetFlagSource(key);
+      // A cvar this build does not register cannot take a saved value; it keeps
+      // its catalog default (see ReadRegistryValues), so skip it like an override.
       if (source == rex::cvar::Source::kEnvironment || source == rex::cvar::Source::kCommandLine ||
-          !NativeSettingOverrideReason(key).empty()) {
+          !NativeSettingOverrideReason(key).empty() || !rex::cvar::GetFlagInfo(key)) {
         result.overridden.push_back(key);
         continue;
       }
diff --git a/rexlego/src/settings_registry.cpp b/rexlego/src/settings_registry.cpp
--- a/rexlego/src/settings_registry.cpp
+++ b/rexlego/src/settings_registry.cpp
@@ -100,7 +100,10 @@ void AssertOwner(std::thread::id owner) {
 Values ReadRegistryValues() {
   Values result;
   for (const auto& spec : catalog) {
-    const auto raw = rex::cvar::GetFlagByName(spec.key);
+    auto raw = rex::cvar::GetFlagByName(spec.key);
+    // A cvar this build does not register (the FSR 1 presenter settings exist
+    // only in REX_HAS_FIDELITYFX_SDK builds) reads as its catalog default.
+    if (raw.empty() && !rex::cvar::GetFlagInfo(spec.key)) raw = spec.default_value;
     if (raw.empty()) throw std::runtime_error("Native setting is not registered: " + std::string(spec.key));
     auto normalized = Canonical(spec, raw, false);
     if (!normalized.valid) throw std::runtime_error(normalized.error);
```

Optional hunk 3 (`fix-a-commit.patch`):

```diff
diff --git a/rexlego/src/settings_registry.cpp b/rexlego/src/settings_registry.cpp
--- a/rexlego/src/settings_registry.cpp
+++ b/rexlego/src/settings_registry.cpp
@@ -200,7 +200,7 @@ Backend MakeNativeRegistryBackend(std::filesystem::path config_path, SettingAvai
         // change must not silently change them. Temporary explicit overrides
         // and unsupported legacy choices are not new player preferences.
         for (const auto& spec : catalog) {
-          if (!NativeSettingOverrideReason(spec.key).empty()) continue;
+          if (!NativeSettingOverrideReason(spec.key).empty() || !rex::cvar::GetFlagInfo(spec.key)) continue;
           auto normalized = Canonical(spec, current.at(std::string(spec.key)), true);
           if (normalized.valid) patch.push_back({std::string(spec.key), spec.type, std::move(normalized.value)});
         }
```

What the fix deliberately leaves out, to stay minimal:
- The frontend still lists the two FSR 1 rows in a non-FFX build. Editing them fails at write, because
  `SetFlagByName` returns false; that is the existing failed-apply path. A follow-up could deny the rows through
  the `availability` callback, which `legodimensions_app.h:128` currently passes as `{}`, e.g.
  `[](std::string_view key) { return rex::cvar::GetFlagInfo(key) ? std::string{} : std::string("Not available in this build"); }`.
- The catalog still offers `fsr` for `present_effect`, while the non-FFX SDK accepts only `bilinear`. That is existing behaviour.

**Verification** (scratch copies only; `build/agent6/fix-a/make_fix_a.py` and `verify_fix_a.py`):
- `make_fix_a.py` checks the live hashes, requires each replacement target to occur exactly once, and writes `orig/`, `new/` and `new-commit/`.
- `git apply --check`, a real apply, and `-R --check` run on fresh copies of the live files in `apply-test/`.
  `GIT_CEILING_DIRECTORIES` is set, so git cannot resolve paths through the enclosing `C:/Users/<user>/.vscode/projects` repo.
  Each result's hashes match `new/` and `new-commit/`, and `fix-a-commit.patch` also passes `--check` on its own.
- `clang++ -fsyntax-only` with the `build/dev/compile_commands.json` flags passes. `-o`, `-MD` and `-MF` are stripped,
  so nothing is written to `build/dev`.
  - Both `new-commit/rexlego/src/settings_registry.cpp` (hunks 1 and 3) and `new/rexlego/src/settings_preferences.cpp`
    return rc=0 with 0 errors.
  - The warnings match the unpatched copies exactly: the same 4 existing `getenv`/`sscanf` deprecation warnings in
    `settings_registry.cpp` (lines 133/135/148/152, which become 136/138/151/155), and none in `settings_preferences.cpp`.
- The live files are unchanged (`A3733700…`, `C78112AA…`).

## Status at the 01:20 relaunch pause, and how to apply at GO

**Decision.** Agent 1 (about 01:20) chose **(a) `fix-a.patch`** (hunks 1 and 2) as the S3 native fix. Hunk 3
(`fix-a-commit.patch`) was not selected and stays optional. Option (b) is parked as a later FSR 1 option: Agent 7's
ODR check found it clean in practice but formally an ODR violation. Agent 6 applies fix A to the live tree
**only at Agent 1's GO after the relaunch**. Agent 10 rates (a).

**Scope for OFF builds (static check, 01:21).** Both files are compiled by OFF builds as well
(`build/agent2/snap1-off/compile_commands.json` has entries; `snap1-on` and `probe-toggle` do too), so S3 changes an
input of the devoff builds. However, the only callers of `MakeNativeRegistryBackend` and `LoadNativePreferences`
are `legodimensions_app.h:128,133`, inside `#ifdef LEGODIMENSIONS_NATIVE_GPU` (lines 105-170).
`settings_frontend.cpp:53,71` and `ui_theme.cpp:351` use only `NativeSettingsCatalog()`, which is static data.
So OFF builds get different object code but never execute the changed lines.

**Apply at GO.** Use a hash-guarded copy of the verified patched files, the same method as S1+p1 and Agent 4's
draw.cpp edit. Do no git writes. Run it from the workspace root:

```powershell
$root = '<workspace>'
$map = @(
  @{rel='rexlego\src\settings_registry.cpp';    before='A37337001EBDC277B2B94D783939A47096423F0AE8962C8B879A6A60B4F8BA4B'; after='8BA19C5F9AC2090FD6921CE01A05EAA8AB648CD3718DF68EEAF8A372BE4A4DB5'},
  @{rel='rexlego\src\settings_preferences.cpp'; before='C78112AA6E50F79D8E6154A37E47CC129C43EAD2E39EC066927374EFBF34B5F0'; after='9CBE6DBF9CEDA62D61469235A828B84017340D356C166335BF53E9AB18565730'}
)
foreach ($m in $map) {   # guard: every check must pass before anything is written
  $live = Join-Path $root ('DimensionsRecomp\' + $m.rel); $new = Join-Path $root ('build\agent6\fix-a\new\' + $m.rel)
  if ((Get-FileHash -Algorithm SHA256 $live).Hash -ne $m.before) { throw "live $($m.rel) is not at the before-hash" }
  if ((Get-FileHash -Algorithm SHA256 $new).Hash -ne $m.after) { throw "patched copy $($m.rel) is not at the after-hash" }
}
foreach ($m in $map) {
  [IO.File]::WriteAllBytes((Join-Path $root ('DimensionsRecomp\' + $m.rel)),
                           [IO.File]::ReadAllBytes((Join-Path $root ('build\agent6\fix-a\new\' + $m.rel))))
}
foreach ($m in $map) {
  $h = (Get-FileHash -Algorithm SHA256 (Join-Path $root ('DimensionsRecomp\' + $m.rel))).Hash
  '{0} {1} {2}' -f $m.rel, $h, $(if ($h -eq $m.after) { 'OK' } else { 'MISMATCH' })
}
```

- Undo: the originals are byte-identical to `build/agent6/fix-a/orig/rexlego/src/*`, at the before-hashes above.
  Copy them back the same way.
- After applying, report to Agent 1, Agent 2 (S3 input: the two relpaths with their before/after hashes) and Agent 10.
  Then update this file.
- At the pause (01:20), the live files were still at the before-hashes (`A3733700…`, `C78112AA…`). The patched
  copies were at `8BA19C5F…` and `9CBE6DBF…`, and `fix-a.patch` was at `71AEFF3D…`.

## Applied at GO (session 3, 2026-11-22 02:05)

Agent 1 gave the GO at about 02:04 for **fix-a + fix-a-commit** (hunks 1-3). Agent 10 §12 rated both SAFE and
recommended the commit hunk. The method was `build/agent6/fix-a/apply_fix_a.ps1 -Apply`: hash-guarded byte copies, with
the same guards as the snippet above plus a check of the undo copies, and every guard passes before the first write.
It writes with `WriteAllBytes`, so both files get mtime 02:05:27 and ninja recompiles them. No git writes.

| File (game repo `DimensionsRecomp/`) | Before | After | Copied from | Size | git blob HEAD → work tree |
|---|---|---|---|---|---|
| `rexlego/src/settings_registry.cpp` | `A3733700…` | `4EC71328043FA6BA8C198D5AAFBFB7D0265CD1939ECE13D1CE11B6A7A48DB77D` | `new-commit/` (hunks 1 and 3) | 10,951 → 11,224 B | 4b56537 → a299f41 |
| `rexlego/src/settings_preferences.cpp` | `C78112AA…` | `9CBE6DBF9CEDA62D61469235A828B84017340D356C166335BF53E9AB18565730` | `new/` (hunk 2) | 4,739 → 4,938 B | 2d72eac → f02940c |

Checks:
- **Pre-check** at 02:02 and 02:05:24: both live files were at the before-hashes (mtime 11-21 10:57:52) and equal to
  the HEAD `a0bdaa7` blobs (`git hash-object` = `git rev-parse HEAD:<path>`). The staged and undo copies were at their hashes.
- **Post-check** at 02:05:28 (`-Check`): both files APPLIED.
- **Read-only git** (`--no-optional-locks`): `diff HEAD` shows exactly hunks 1-3 (registry +5/-2, prefs +3/-1), and
  `status --porcelain -- rexlego/src` lists only these two files.
- **Syntax:** `build/agent6/fix-a/syntax_live.ps1 -Tag post` runs `env/compile-one.ps1 -SyntaxOnly` with
  `build/dev/compile_commands.json` (NATIVE_GPU=1), one clang at a time.
  - registry: rc=0, 0 errors. The only warnings are the same 4 existing `getenv`/`sscanf` deprecation warnings, now at
    lines 136/138/151/155, as predicted.
  - prefs: rc=0, 0 warnings.
  - Log: `build/agent6/fix-a/syntax-post.log`.

Undo: `powershell -NoProfile -File build\agent6\fix-a\apply_fix_a.ps1 -Revert`. It copies `orig/` back, but only if
the live files are at the after-hashes. `-Check` reports the state at any time without writing anything.

For S3: every S3 arm keeps `--native_settings_load=false` (Agent 10 §12). OFF builds compile both files but never run
the changed lines. Proof for native3 is the boot without the workaround flag (Agent 7 checks: frontend on, no throw,
bilinear present).

**Proven at runtime (02:57, Agent 8's slot): `build/agent8/runs/0256-native3` PASS.** Agent 8 reports, and I spot-checked
(read-only):
- The toml sets `native_settings_frontend = true`, and the workaround flag is not used.
- `game.log` passes the old crash point, "Native write tracking" (line 44), and reaches "Native settings graph bound:
  generation=1" (line 410). That means `NativeSettingsRuntime` was constructed.
- There is no "not registered", `0xE06D7363` or `[FATAL]` line, and there are 0 dumps. The game closed cleanly with
  WM_CLOSE.
- The MANIFEST lists fix (a) at 4EC71328 / 9CBE6DBF, and the native GPU fingerprint 8f849b69907d4006 matches `game.log`.
- `bench/agent7/native3_boot_check.py`: PASS (Agent 7).
