# S3 proposal: native startup crash fix (Agents 7, 6 and 2)

**Decision (Agent 1, ~01:20): S3 uses (a), `fix-a.patch`. Agent 6 applies it at Agent 1's GO after the agy-grid relaunch. (b) is parked as a later FSR 1 option.**

**Agent 10's ratings (01:25, `perf-notes/agent10-batch2-review.md` §12):** fix-a.patch is SAFE (hunks 1 and 2 must ship together), and fix-a-commit.patch is SAFE and recommended. My one-line alternative in §(a) is NOT SAFE as written, so it is dropped. Agent 10 agrees with the (b) ODR analysis. If (b) is revived:
- re-run Agent 10's grep guard before the build;
- add Agent 10's hazards 6 (COMDAT pick) and 7 (LTO) to the note for the owner.

**v3 (final for Agent 1), Agent 7, 00:01. Recommendation updated at 00:20, after Agent 1's ODR/layout question (00:02); the check is in `perf-notes/agent7-odr-ffx.md`.** Text only: no builds or tree edits before window 3 ends.

Inputs:
- **(a):** Agent 6's verified Fix A patch. The canonical text is in `perf-notes/agent6-crash-triage.md`, "Fix A as a unified diff".
- **(b):** Agent 7's plan; Agent 2 checked and corrected the build side in place at 00:33 (build dir confirmed, ~2-3 min, separate native3ffx-bin, automatic revert).

Context: `ReadRegistryValues` throws at boot for `present_fsr_sharpness_reduction` when `native_settings_frontend=true`, which is the shipped NativeGPU 0.2.0 default. The key isn't registered because every SDK build here has FidelityFX off. Window 3 runs `--native_settings_frontend=false`. With that flag:
- the renderer uses the legacy direct-cvar path;
- the present stays bilinear.

## Recommendation

**Updated 00:20: use (a) for S3, as Agent 1 proposes. (b) passed the layout check and stays available.**
- **ODR/layout check** (`perf-notes/agent7-odr-ffx.md`):
  - every FidelityFX-dependent member, array and enum count is touched only inside rexui (`rexruntime.dll`);
  - code outside rexui only holds pointers or makes virtual or out-of-line calls;
  - the owner's stock FidelityFX build has the same mix, plus the RUNTIME members.
  So (b) has no layout blocker. It is still a formal ODR violation, though, and (a) has no binary mix at all.
- **(a):** Agent 6's `fix-a.patch`, plus `fix-a-commit.patch` if wanted. It gives frontend on with a bilinear present. It goes to Agent 10 for rating.
- **(b), if Agent 1 wants native runs in the shipped FSR 1 config:** set only `REXGLUE_FIDELITYFX_SOURCE_DIR` for the native SDK and keep `REXGLUE_ENABLE_FIDELITYFX=OFF`, then stage that `rexruntime.dll` as native3ffx-bin, a copy of native3-bin with only the runtime swapped (§(b) Staging). If its compile or checks fail, fall back to (a), or keep `--native_settings_frontend=false`.

v3 (00:01) recommended (b), for these reasons:
1. **Shipped config.** native3 then runs the shipped config: frontend on, FSR 1 present. The run toml already selects FSR 1 (`present_effect='fsr'`, passes 1, sharpness reduction 0.0). With (a), the game boots with the frontend on, but FSR 1 stays off (`present_effect` only allows bilinear). Native runs would keep measuring a bilinear present that default-config players don't get.
2. **No source change.** There is nothing for Agent 10 to rate and nothing for the owner to take. The FidelityFX branch is the owner's own build config.
3. **Small, contained cost.** 35 rexui TUs plus its PCH and a `rexruntime.dll` relink, after the normal S3 pipeline: ~2-3 min at -j10 (Agent 2, §(b) Timing; v3 guessed ~5-7 min). The OFF builds are untouched.
4. **(a) can still go later.** (a) does nothing in any FidelityFX build, because all 17 catalog keys are registered there. So it can go to the owner later without changing any measurement.

**Caveat for both options: comparisons with window 3.**
- Window 3 measures native-bin/native2-bin with the frontend off and a bilinear present. For cross-build deltas against that data, pin native3 runs with `--native_settings_frontend=false --present_effect=bilinear`.
- Shipped-config numbers come from native3 with its defaults.
- My present item (b), the clear skip, only applies outside FSR 1 (`device.cpp:2058`). So it only shows up in the pinned runs.

## (a) Code fix: Agent 6's Fix A, for Agent 10 to rate

Patches are in `build/agent6/fix-a/` (CRLF, paths relative to `DimensionsRecomp/`).

- **`fix-a.patch`** (sha256 `71AEFF3D…`): hunks 1 and 2, the requested fix.
  - **Hunk 1**, `rexlego/src/settings_registry.cpp:103-104` (`ReadRegistryValues`):
    - An unregistered catalog key (`GetFlagByName` returns "" and `GetFlagInfo` returns null) reads as `spec.default_value` instead of throwing.
    - `Values` stays complete, so `Decode` works.
    - A registered cvar with an empty value still throws.
  - **Hunk 2**, `rexlego/src/settings_preferences.cpp:69-71` (`LoadNativePreferences`): a saved value for an unregistered key is skipped like an override. Without hunk 2:
    1. hunk 1 lets a saved non-default FSR 1 value reach `backend.write`, which fails;
    2. the rollback fails the same way;
    3. `recovery_failed` leads to `QuitFromUIThread` (`legodimensions_app.h:138-141`).
    This only matters with `native_settings_load=true`.
- **`fix-a-commit.patch`** (sha256 `50046A3F…`): optional hunk 3 at `settings_registry.cpp:200`. The commit loop skips unregistered keys, so a FidelityFX-off build never writes the FSR 1 defaults over values that a FidelityFX build saved.
- **Patched copies:** full copies are in `build/agent6/fix-a/new/` and `new-commit/`. The before/after sha256 table is in Agent 6's notes.
- **Verified on scratch copies:**
  - `git apply --check`, apply and `-R --check` all pass;
  - `clang++ -fsyntax-only` with the build/dev flags returns rc=0, with only the 4 existing deprecation warnings;
  - the live files are unchanged.

Agent 7's notes on (a):
- **Scope.** Behaviour is identical whenever every catalog key is registered, which is every FidelityFX build, including (b). Combined with (b), (a) is dead code.
- **Linkage.** `GetFlagInfo` (`rex/cvar.h:234`) is exported by `rexruntime.dll`: its mangled name sits next to `GetFlagByName` and `GetFlagSource` in native2-bin's DLL. So the exe's new import resolves. No rexlego code uses it today.
- **What it leaves out.**
  - In FidelityFX-off builds, FSR 1 stays off: `settings->fsr1` is false at `device.cpp:2048`.
  - The menu still lists the FSR 1 rows and the 'fsr' choice. Editing them fails at Apply, which is the existing failed-apply path.
  - Agent 6's suggested follow-up would deny those rows through the availability callback (`legodimensions_app.h:128`).
- **Alternative for Agent 10 to weigh: DROPPED, NOT SAFE as written** (Agent 10, `perf-notes/agent10-batch2-review.md` §12). `Transaction::Defaults()` (`settings_transaction.cpp:47-70`) normalizes all 17 catalog keys through registry :169, which calls `NativeSettingOverrideReason`. With this line, "Restore defaults" would always fail in builds without FidelityFX. A working variant would accept only the catalog default for an unregistered key. Original text (untested; Agent 6's patch is the verified one): add one line at the top of `NativeSettingOverrideReason` (`settings_registry.cpp:131`):
  `if (!rex::cvar::GetFlagInfo(key)) return "Setting is not available in this build";`
  This line would:
  - replace hunks 2 and 3, through the override checks that already exist at `settings_preferences.cpp:71` and `settings_registry.cpp:200`;
  - also reject edits of the FSR 1 rows with a reason, through the validate lambda (169-171) and Save (189-190).
- **Cost.** 2 TUs per game build.

## (b) FidelityFX-ON rexruntime for native only

**Agent 2 checked the build side and corrected it here at 00:33.** It was a read-only check: snap1's CMake files and headers, plus `build/agent2/snap1-sdk` (impl-Release.ninja, the S2 `.ninja_log` and the configure logs). Nothing was built or run. Since 00:20 the Recommendation is (a) for S3, so this is the build plan in case Agent 1 picks (b).

### Configure
- **Build dir: reuse `build/agent2/snap1-sdk` (confirmed).** The SDK always builds from snap1, even when B's game builds from snapB:
  - snapB holds only the game side and builds against `snap1-sdk/install`, so it has no SDK build dir;
  - the flag below therefore always names snap1's FidelityFX-SDK.
- **A second build dir doesn't help.** `rexglue-sdk/CMakeLists.txt:258-260` puts every SDK binary in `<tree>/rexglue-sdk/out/win-amd64/<Config>`, whatever `-B` says. A second dir would share `out/` and still compile every rexruntime dependency from scratch.
- **When:** after the S3 SDK install and the devoff3 and native3 game builds. The game trees link `snap1-sdk/install`, which this step never touches, so B can run before or after it.
- **Commands.** Only one cache value changes:
  1. `cmake -S build/agent2/snap1/DimensionsRecomp/rexglue-sdk -B build/agent2/snap1-sdk -DREXGLUE_FIDELITYFX_SOURCE_DIR=<workspace>/build/agent2/snap1/DimensionsRecomp/rexglue-sdk/thirdparty/FidelityFX-SDK`
  2. `cmake --build build/agent2/snap1-sdk --config Release --target rexruntime -j 10`
  - Build the `rexruntime` target only, and never run `install`.
  - The headers exist in snap1: `sdk/include` and `ffx-api/include`, at eee08db, which is `rexglue_fidelityfx.cmake`'s GIT_TAG.
  - With ENABLE OFF, `rexglue_fidelityfx.cmake` returns at lines 7-8 and never touches the variable. It only sets it (CACHE INTERNAL, line 61) when ENABLE is ON. So the cache entry is exactly the value `-D` gives.
- **Effect:**
  - `rexglue_fidelityfx.cmake` returns at line 7 because ENABLE is OFF, so nothing is fetched or built from FidelityFX.
  - `ui/CMakeLists.txt:122-128` adds the two include dirs and `REX_HAS_FIDELITYFX_SDK=1` to rexui, as PRIVATE.
  - There are no `amd_fidelityfx_*` targets, so:
    - no `REX_HAS_FIDELITYFX_RUNTIME` (`ui/CMakeLists.txt:130-141`);
    - no `/DELAYLOAD` in `rexruntime.dll` (`src/rexglue/CMakeLists.txt:31-39`);
    - no POST_BUILD copy of a FidelityFX DLL (`rexglue_helpers.cmake:130-141`).
  - `presenter.cpp:43-73` then registers:
    - `present_effect` {bilinear, cas, fsr, fsr2, fsr3}, default bilinear;
    - `present_cas_additional_sharpness`;
    - `present_fsr_max_upsampling_passes`;
    - `present_fsr_sharpness_reduction`;
    - `present_fsr_quality_mode`.

**Why not `REXGLUE_ENABLE_FIDELITYFX=ON`:**
- **Fetch:** FetchContent does a full clone (GIT_SHALLOW OFF; Agent 2 measured ~115 KB/s), unless `FETCHCONTENT_SOURCE_DIR_FIDELITYFX` is set.
- **Build:** ffx-api builds from source with `FFX_API_AUTO_COMPILE_SHADERS=ON`.
- **Runtime:** rexui gets `REX_HAS_FIDELITYFX_RUNTIME`, and `rexruntime.dll` gets a delay-load of `amd_fidelityfx_dx12.dll`.
- **DLL swap:** the POST_BUILD copy would put a self-built `amd_fidelityfx_dx12.dll` next to the exe. It would replace the prebuilt signed copy (`12A50812…`) that native FSR 3 uses.

Native needs none of this. Native FSR 1 is the exe's own code (`gpu_native/fsr1_present.h`, `device.cpp:2048-2066`). It only needs the cvars registered and 'fsr' allowed.

### What rebuilds (checked)
- **rexui: 35 TUs plus its own PCH.**
  - rexui is an OBJECT library (`ui/CMakeLists.txt:99`) with a PRIVATE PCH: `rex_target_pch(rexui <rex/math.h>)`, no REUSE_FROM.
  - The new define and include dirs are PRIVATE too.
- **`rexruntime.dll` relinks.** In impl-Release.ninja, the only link edges with rexui objects are `rexruntime{,d,rd}.dll`.
- **Not rebuilt:**
  - `rexgpu-xenos.dll` and `rexglue.exe`, because the build is `--target rexruntime`. Building `all` would relink them against the new import lib, which isn't needed.
  - No game TU, and the exe doesn't relink.
- **Side effect of any reconfigure:** `rex/version.h` is regenerated, because `REXGLUE_BUILD_TIMESTAMP` has minute resolution (`CMakeLists.txt:250`).
  - Its includers are rexui's `rex_app.cpp` and `debug_overlay.cpp`, which rebuild anyway, and three `rexglue.exe` TUs.
  - So the build string in the FFX DLL's overlay carries a new timestamp. This is harmless.

### Timing
| Part | Time | Source |
| --- | --- | --- |
| rexui | ~35-40 s at -j10 | S2 `.ninja_log`: PCH 13.3 s, then 35 TUs totalling 266 s CPU; longest `settings_overlay.cpp`, 22.7 s |
| `rexruntime.dll` link | 10.8 s | S2 `.ninja_log` |
| Reconfigure | budget 30-60 s | Not measured on this tree. The fresh configure took 235.5 s (19:46, 4 CPUs), mostly checks the cache now holds. Generation alone is 12.6 s. |
| Copy, checks, staging | ~30 s | |

- **Total: ~2-3 min, not 5-7.**
- The revert (Staging step 5) costs about the same reconfigure plus the rexui rebuild, ~1.5 min. That time falls inside S4's SDK phase.

### Staging (corrected: a separate native3ffx-bin instead of an in-place swap)
1. **Save the FFX pair right after the build.** Copy `rexruntime.dll` and `rexruntime.pdb` from `snap1/DimensionsRecomp/rexglue-sdk/out/win-amd64/Release/` to `build/agent2/ffx3-rt/`, with sha256. The next SDK build overwrites `out/`.
   - Don't use `cmake --install --prefix …/install-ffx`: it copies the whole SDK, including `out/` binaries this step didn't rebuild.
2. **native3-bin:** stage it as usual, with the OFF rexruntime and the full artifact checks. It runs the same runtime as native2-bin, so comparisons pinned to the window-3 flags stay clean.
3. **native3ffx-bin:** a copy of native3-bin with only `rexruntime.dll`/`.pdb` replaced. For scale, native2-bin is 9 files, 364 MB.
   - Its own MANIFEST records both rexruntime sha256s and "FidelityFX: SOURCE_DIR only (headers), no runtime".
   - It also gives a control: the same exe with the OFF runtime and with the FFX runtime, under the pinned flags.
   - If Agent 1 prefers a single dir, swap into native3-bin after staging, with the same checks.
4. **Checks: Agent 7's list, plus two from Agent 2 (marked new):**
   - the new DLL contains `present_fsr_sharpness_reduction`, `present_fsr_max_upsampling_passes` and "Guest output effect: bilinear, cas, fsr, fsr2, fsr3";
   - `rexruntime.dll` doesn't import `amd_fidelityfx_dx12.dll` (`llvm-readobj --coff-imports`);
   - every name that `legodimensions.exe` **and `rexgpu-xenos.dll`** import from `rexruntime.dll` is exported by the new DLL. The exe was linked against the OFF import lib, and the FidelityFX branch only adds exports (`FLAGS_present_effect_storage_` exists in both branches). (New: `rexgpu-xenos.dll` also links `rexruntime.lib` and isn't rebuilt);
   - new: in native3ffx-bin, every file except the swapped pair is byte-identical to native3-bin's;
   - in compile_commands.json, rexui entries gain `REX_HAS_FIDELITYFX_SDK=1` and the two `-I` dirs, with no `REX_HAS_FIDELITYFX_RUNTIME`, and no other target's entries change.
5. **Revert: automatic, not a manual `-U`.** `cmake -U REXGLUE_FIDELITYFX_SOURCE_DIR build/agent2/snap1-sdk` would work, because the entry only exists because of `-D`. But Agent 2 builds the revert into `build-snap.ps1` instead:
   - every OFF SDK configure passes `-UREXGLUE_FIDELITYFX_SOURCE_DIR`;
   - the SDK install step refuses to run while CMakeCache.txt has a non-empty `REXGLUE_FIDELITYFX_SOURCE_DIR`.
   So the next SDK phase (S4) has to reconfigure (no `-SkipConfigure`). An FFX DLL can't reach `snap1-sdk/install` or any devoff build.
6. **Functional boots** in Agent 8's slot:
   - **Default run toml** (frontend on, `present_effect='fsr'`): expect no throw at NativeSettingsRuntime, and the FSR 1 present path.
   - **Window-3 flags:** a second boot with those flags.

### Risks
- **Untested compile.** rexui's FidelityFX branch hasn't been compiled here. The owner builds it, and the headers are the CMake file's pinned tag.
  - If the compile fails, ninja stops before the relink. `out/` keeps the OFF `rexruntime.dll`, and the revert rebuilds the partly rebuilt rexui objects.
- **Presenter layout.** `Presenter`'s layout differs inside rexui (`presenter.h:317-322`, four FidelityFX members, plus the arrays sized by the effect counts) from code outside rexui that includes `presenter.h` (graphics_system.h, command_processor.h, window.h, d3d12_presenter.h). The owner's FidelityFX build has the same split. **Checked at 00:20** (`perf-notes/agent7-odr-ffx.md`): clean in practice, because only rexui touches the changed members.
  - **Agent 2's separate read of snap1 agrees:**
    - **What differs:** `GuestOutputPaintConfig` gains 4 data members (`presenter.h:317-322`), and `Presenter` holds one as the private `guest_output_paint_config_` (line 938). `kMaxGuestOutputPaintEffects` (473-484) and `GuestOutputPaintEffect::kCount` change, and with them `GuestOutputPaintFlow` and D3D12Presenter's arrays (`d3d12_presenter.h:198, 245, 288-290`).
    - **What crosses the boundary:** `rexgpu-xenos.dll` (`src/graphics/d3d12/command_processor.cpp:2199-2538`) uses only the presenter pointer, the virtual `RefreshGuestOutput`, `D3D12GuestOutputRefreshContext` (no FFX-dependent members) and static constants.
    - **Why it stays inside rexui:** no FFX block in presenter.h declares a virtual, so the vtables match. The only inline body that touches the moved members is private (line 1010). The object is allocated in rexui (`d3d12_provider.cpp:516` calls the inline `D3D12Presenter::Create`), and `graphics_system.cpp:112-115` gets it through the virtual `CreatePresenter`. A git grep finds no use of `GuestOutputPaintConfig`/`Flow`/`Effect` or `kMaxGuestOutputPaintEffects` in `rexglue-sdk/src` outside `src/ui`, or in `rexlego/src`.
- **Comparability.** The FSR 1 present adds GPU work on the MX570: EASU, 1 pass, plus RCAS at 2240x1294. So native3 runs with defaults can't be compared with window-3 numbers; use the pinned flags for cross-build deltas.

## Timeline
- **Window 3** (00:15 to ~01:00-01:15): nothing runs.
- **After window 3:** Agent 2's S3 pipeline, as for S2. If (b) is picked, add ~2-3 min, plus ~1.5 min in S4's SDK phase for the revert.
- **Agent 10:** rates (a) and the (b) ODR analysis (sent at 00:20).
