# ODR/layout check for S3 option (b): FidelityFX define in rexui only

**Agent 7, 00:20, text only (quiet window 3: no commands run).** For Agent 1 (request at 00:02) and Agent 10 (rating). Paths are relative to `DimensionsRecomp/rexglue-sdk/` unless noted. Line numbers are from the live tree (re-read at 00:13).

Evidence (greps, CMake reads and symbol scans, all made before 00:10) is in `C:/Users/<user>/.gemini/antigravity-cli/brain/f32c69f9-1f5c-4e55-a490-0379b0dfd6de/scratch/odr/`: `ui-headers.txt`, `users-outside-rexui.txt`, `paintconfig-users.txt`, `mangled-rexruntime.txt`, `mangled-rexgpu-xenos.txt`, `exe-map-presenter.txt`, `exe-map-objects.txt`, `cmakelists.txt`, `install-defs.txt`.

## Answer
1. **Layout-dependent items** are all in three headers: `include/rex/ui/presenter.h`, `d3d12/d3d12_presenter.h` and `vulkan/presenter.h` (Vulkan isn't compiled here). The full list is in §2. The ones that change object layout:
   - `GuestOutputPaintConfig` (12 → 28 B);
   - every `Presenter` member after `guest_output_paint_config_` (+16 B);
   - `GuestOutputPaintFlow`;
   - the D3D12Presenter arrays and `PaintContext`.
   No virtual function is guarded, so the vtables are the same.
2. **Users outside rexui** (§3):
   - rexgpu-xenos.dll, which native mode doesn't load;
   - header-only pointer users in other rexruntime code;
   - in the exe: rex_app.cpp (pointer only) and rexlego (no SDK presenter at all).
   None of them touches a layout-dependent item. They use pointers, `unique_ptr` with the virtual dtor, virtual calls, the exported out-of-line `RefreshGuestOutput`, `D3D12GuestOutputRefreshContext` (unchanged) and static constexpr DXGI constants (unchanged).
3. **Owner's stock build** (§5): same mix, plus the RUNTIME members. (b) is a subset of it.
4. **Verdict:** clean in practice, but still a formal ODR violation, with latent hazards (§4). I agree with **(a) for S3**. (b) has no layout blocker.

## 1. What is compiled where

| Binary | Contents | `REX_HAS_FIDELITYFX_SDK` with (b) | Loaded in native mode |
|---|---|---|---|
| `rexruntime.dll` | rexui is an OBJECT library (`src/ui/CMakeLists.txt:99`) linked into rexruntime (`src/graphics/CMakeLists.txt:135-137`); the Presenter and D3D12Presenter vtables, ctors and methods are in this DLL (`mangled-rexruntime.txt`). Plus all other SDK runtime objects. | rexui TUs only (PRIVATE, `src/ui/CMakeLists.txt:122-127`) | yes |
| `rexgpu-xenos.dll` | SHARED plugin (`src/graphics/CMakeLists.txt:101`), loaded by `rex::system::LoadGpuPlugin`, links rexruntime PRIVATE: graphics_system.cpp, command_processor.cpp, d3d12/graphics_system.cpp, d3d12/command_processor.cpp | no | no (xenos mode only) |
| `legodimensions.exe` | rexlego, plus two SDK sources compiled into the exe: `rex_app.cpp` and `windowed_app_main_sdl.cpp` (`rexglue_helpers.cmake:80-82`; the exe map has `rex_app.cpp.obj` and `windowed_app_main_sdl.cpp.obj` as direct objects). The installed INTERFACE defs (`rexglueTargets.cmake:62`) have no FidelityFX define. The game's FidelityFX include dirs (`rexlego/CMakeLists.txt:238-251`) are for native FSR 3 and define nothing. | no | yes |

- **RUNTIME define:** `REX_HAS_FIDELITYFX_RUNTIME=1` (PRIVATE, `src/ui/CMakeLists.txt:130-141`) only comes with the `amd_fidelityfx_*` targets, i.e. with `REXGLUE_ENABLE_FIDELITYFX=ON`. (b) doesn't set it.
- **The split is deliberate:** `rexglue_helpers.cmake:131` says "FidelityFX is linked PRIVATE by rexui (to avoid propagating DLL requirements to tool-mode targets)".
- **No symbol clash:** the exe's own FidelityFX libs (`ffx_backend_dx12_x64`, `ffx_fsr3upscaler_x64`, used by fsr3_upscaler.cpp) are in a different binary from rexui.

## 2. Everything whose type or size depends on the guards
`REX_HAS_FIDELITYFX_*` appears only in these three headers and in rexui's own .cpp files (presenter.cpp, d3d12_presenter.cpp, vulkan_presenter.cpp). Source: a grep of all SDK `src/` and `include/` plus `rexlego/src`.

### presenter.h (class Presenter and its nested types)

| # | Item | Line | Guard | OFF → (b) | Layout effect |
|---|---|---|---|---|---|
| P1 | `GuestOutputPaintConfig::Effect` | 213-229 | SDK | adds kCas=1, kFsr=2, kFsr2=3, kFsr3=4 (kBilinear=0 in both) | values only, still 4 B |
| P2 | `GuestOutputPaintConfig::FsrQualityMode` and the CAS/FSR constants | 231-263 | SDK | only with SDK | none (types and constants) |
| P3 | CAS/FSR inline getters and setters | 276-302 | SDK | only with SDK | none (non-virtual) |
| P4 | **config data members** `cas_additional_sharpness_`, `fsr_max_upsampling_passes_`, `fsr_sharpness_reduction_`, `fsr_quality_mode_` | 317-322 | SDK | added | **sizeof(GuestOutputPaintConfig) 12 → 28**: `dither_` moves from offset 8 to 24; `allow_overscan_cutoff_` @0 and `effect_` @4 stay |
| P5 | `GuestOutputPaintEffect` | 427-441 | SDK | 7 values added after kBilinearDither; **kCount 2 → 9** | sizes D5 and the Vulkan arrays |
| P6 | `CanGuestOutputPaintEffectBeIntermediate/Final` | 443-471 | SDK cases | n/a | none (constexpr) |
| P7 | `kMaxGuestOutputPaintEffects` | 473-484 | SDK | **1 → 6** | sizes P8, D3, D4 |
| P8 | `GuestOutputPaintFlow::effects`, `effect_output_sizes` | 501-502 | via P7 | 1 → 6 elements each | sizeof(GuestOutputPaintFlow) grows; returned by the protected `GetGuestOutputPaintFlow` (678) |
| P9 | CAS/FSR effect constant structs (`Initialize(flow, i, config)`) | 551-618 | SDK | only with SDK | none |
| P10 | **`Presenter::guest_output_paint_config_`** | 938 | via P4 | its own offset is unchanged (nothing earlier changes) | **every later Presenter member moves +16 B**, from `guest_output_mailbox_acquired_and_ready_` (953) through the UI-drawer and DXGI tick members. 16 is a multiple of every member alignment (≤ 8), so the shift is exactly 16 and **sizeof(Presenter) grows by exactly 16** |
| n/a | virtual functions | n/a | none guarded | n/a | **vtable order identical** |

### d3d12/d3d12_presenter.h (class D3D12Presenter final : Presenter)

| # | Item | Line | Guard | OFF → (b) | Layout effect |
|---|---|---|---|---|---|
| D1 | `GuestOutputPaintRootSignatureIndex` | 133-143 | SDK | **kGuestOutputPaintRootSignatureCount 1 → 5** | sizes D5 |
| D2 | `GetGuestOutputPaintRootSignatureIndex` | 145-168 | SDK cases (151) | n/a | none |
| D3 | `PaintContext::kViewCount` (= 3 + kMax - 1) | 198 | via P7 | 3 → 8 | descriptor heap size (rexui code) |
| D4 | `PaintContext::guest_output_intermediate_textures` (`std::array<ComPtr, kMax - 1>`) | 245-246 | via P7 | 0 → 5 | sizeof(PaintContext) grows; later PaintContext members move |
| D5 | `guest_output_paint_root_signatures_` [D1 count]; `guest_output_paint_intermediate_pipelines_` and `guest_output_paint_final_pipelines_` [P5 kCount] | 286-291 | via D1, P5 | 1 → 5; 2 → 9 each (ComPtr) | later members move |
| D6 | all D3D12Presenter members | n/a | via P10 | +16 (base), then D4/D5 growth | sizeof(D3D12Presenter) grows |
| R1 | `EnsureTemporalUpscalerContext`, `DispatchTemporalUpscaler`, `DestroyTemporalUpscalerContext` | 265-274 | RUNTIME | not in (b) | none (private, non-virtual declarations) |
| R2 | trailing `temporal_upscaler_*` members | 315-322 | RUNTIME | not in (b) | sizeof grows at the end (owner's FFX build only) |

Unchanged:
- `D3D12UIDrawContext` (26-44);
- the static constexpr guest output format and states (48-55);
- `D3D12GuestOutputRefreshContext` (58-70: the base `bool&` plus a ComPtr).

### vulkan/presenter.h (class VulkanPresenter): not compiled here (`REXGLUE_USE_VULKAN=OFF`)
- `GuestOutputPaintPipelineLayoutIndex` count 1 → 5 (231-241), and its switch (243-265, SDK guard at 249).
- Descriptor-set count via kMax (320).
- Arrays sized by kCount or kMax - 1 (372, 393, 396) and by the layout count or kCount (455, 458).
- RUNTIME functions (438-444) and trailing members (484-).

It's the same pattern as D3D12: only vulkan_presenter.cpp uses these. `vulkan/command_processor.h:705` is sized by `kMaxActiveGuestOutputImageVersions`, which doesn't depend on FidelityFX.

## 3. Users outside rexui

| User | Where | Binary | Native? | Access | Layout-dependent? |
|---|---|---|---|---|---|
| GraphicsSystem owns the presenter | `graphics_system.h:134` `std::unique_ptr<Presenter> presenter_`; `graphics_system.cpp:112/115` `provider_->CreatePresenter(loss_cb)`; `:215/:220` `presenter_.reset()` | rexgpu-xenos | not loaded | virtual `CreatePresenter` (`graphics_provider.h:48`) → `D3D12Provider::CreatePresenter` (rexui) → inline `D3D12Presenter::Create` (`d3d12_presenter.h:72-80`), instantiated in rexui; deletion goes through the virtual dtor, whose deleting dtor is in rexui | no |
| presenter getters | `graphics_system.h:59/64` | rexgpu-xenos | not loaded | pointer | no |
| IssueSwap | `d3d12/command_processor.cpp:2199-2201` (`presenter()`), `2285-2288` (`RefreshGuestOutput(..., std::function<bool(GuestOutputRefreshContext&)>)`) | rexgpu-xenos | not loaded | out-of-line call exported by rexruntime.dll, the DLL's only Presenter import (`mangled-rexgpu-xenos.txt`) | no |
| refresher lambda | `d3d12/command_processor.cpp:2407/2419` (`static_cast<D3D12GuestOutputRefreshContext&>`, `resource_uav_capable()`); `2418/2427/2479-2538` (`kGuestOutputInternalState`, `kGuestOutputFormat`) | rexgpu-xenos | not loaded | unchanged class; unguarded static constexpr | no |
| Vulkan command processor | `vulkan/command_processor.cpp`, `.h` | none | not compiled | same pattern | no |
| system graphics interface | `include/rex/system/interfaces/graphics.h:26/59` (forward declaration, `virtual ui::Presenter* presenter() const`) | rexruntime (non-rexui) | yes | pointer | no |
| `graphics/command_processor.h:31` | include only | rexgpu-xenos | not loaded | none | no |
| Window, ImGuiDrawer, ImmediateDrawer, UIDrawContext (headers, also included by the exe) | `window.h:358` (`SetPresenter`, out-of-line), `369-371` (inline wrapper that calls the out-of-line `RequestUIPaintFromUIThread`), `559`, `735`; `imgui_drawer.h:56-60, 110`; `immediate_drawer.h:97, 126, 142`; `presenter.h:64-86` | all | yes | pointer, out-of-line | no |
| ReXApp | `rex_app.cpp`, compiled into the exe; `SetupOverlays(ui::Presenter*, ui::ImmediateDrawer*)` (`rex_app.h:270`) | exe | yes | pointer; the exe's only Presenter-related imports are the `SetPresenter` functions of ImGuiDrawer, ImmediateDrawer and Window (`exe-map-presenter.txt`) | no |
| rexlego gpu_native | `device.cpp` (includes window.h, debug_overlay.h), `native_overlay.cpp` (imgui_drawer.h, immediate_drawer.h; detached, presenter-less mode, `rex_app.h:177-189`) | exe | yes | no `rex::ui::Presenter` object; present settings are read by cvar name (`device.cpp:2048-2066`, `FLAGS_present_effect_storage_` import) | no |

`Fsr1Presenter` (`gpu_native/fsr1_present.h:23`, `device.cpp:250, 2063-2069`) and `DisplayGammaGpu` (`device.cpp:251, 2018-2023`) are the exe's own classes, unrelated to `rex::ui::Presenter`.

**Not used outside rexui** (grep over SDK src/include and rexlego/src; no imports in the exe or rexgpu-xenos):
- `GuestOutputPaintConfig`, the inline `GetGuestOutputPaintConfigFromUIThread()` (presenter.h:365) and `SetGuestOutputPaintConfigFromUIThread` (369);
- `FsrQualityMode`, `GuestOutputPaintEffect`, `GuestOutputPaintFlow`, `kMaxGuestOutputPaintEffects`;
- `D3D12Presenter::Create`, whose only caller is `D3D12Provider::CreatePresenter` (rexui);
- `AddUIDrawerFromUIThread`.

**In native mode no SDK presenter object exists at all:** rexgpu-xenos.dll isn't loaded, and rexlego never calls `CreatePresenter`. So in native3-bin, the only thing (b) changes at run time is presenter.cpp's static cvar registration: the CAS/FSR cvars get registered, and 'fsr' becomes a valid `present_effect`. The exe reads those cvars by name.

## 4. Why it holds, and what would break it
It holds because:
- **Allocation:** only rexui allocates presenters.
- **Destruction:** goes through the virtual dtor, which is rexui code.
- **Member access:** every changed member is touched only by code compiled in rexui.
- **Vtables:** the slot order doesn't depend on the guards.
- **Boundary types:** the types that cross the binary boundary don't depend on the define: `Presenter*`, `std::unique_ptr<Presenter>`, `std::function<bool(GuestOutputRefreshContext&)>`, `D3D12GuestOutputRefreshContext&` and the DXGI constants.

It is still **formally an ODR violation**: there are two definitions of `Presenter` in one program, which is ill-formed, no diagnostic required. Nothing checks this, because MSVC-ABI mangled names don't encode class layout.

Latent hazards (none present today):
1. Outside code calls the inline `GetGuestOutputPaintConfigFromUIThread()` and then `GetDither()` (it reads offset 8, not 24), or copies the config (12 of 28 B).
2. Outside code builds a `GuestOutputPaintConfig` and passes it to `SetGuestOutputPaintConfigFromUIThread` (rexui reads 28 B from a 12 B object).
3. Outside code calls `D3D12Presenter::Create` (it would allocate a too-small object) or derives from Presenter.
4. Outside code reads, through an inline accessor, any Presenter member after line 938, or anything sized by `kMaxGuestOutputPaintEffects` or `GuestOutputPaintEffect::kCount`.
5. rexgpu-xenos or the exe starts using any of the "not used" items in §3. `command_processor.cpp` already includes d3d12_presenter.h.

## 5. Owner's stock FidelityFX build: the same mix, plus more
- **Defines:** with `REXGLUE_ENABLE_FIDELITYFX=ON`, rexui gets both `REX_HAS_FIDELITYFX_SDK` and `REX_HAS_FIDELITYFX_RUNTIME`, still PRIVATE (`src/ui/CMakeLists.txt:122-141`). rexgpu-xenos.dll, the other rexruntime objects, `rex_app.cpp`, `windowed_app_main_sdl.cpp` and the game get neither (`rexglueTargets.cmake:62`).
- **So the owner's build has exactly (b)'s SDK mix, plus the RUNTIME mix:** R1, R2, and the Vulkan ones at 438/484.
- **It's exercised upstream:** the owner's build runs in xenos mode, where rexgpu-xenos.dll drives the live presenter every frame (`RefreshGuestOutput`, `command_processor.cpp:2285`). So the access pattern (b) relies on already runs upstream, with a bigger mismatch than (b) has.
- **(b) is a strict subset:** SDK define only, no RUNTIME members, no delay-load.

## 6. Recommendation
- **S3: (a), as Agent 1 proposes.** It:
  - has no binary mix;
  - touches 2 game TUs;
  - fixes the crash in any FidelityFX config.
  For Agent 10: `build/agent6/fix-a/fix-a.patch`, plus the optional `fix-a-commit.patch`. My untested one-line alternative is in agent7-s3-proposal.md §(a).
- **(b): no layout blocker.** Choose it only if Agent 1 wants native runs in the shipped FSR 1 config. In that case:
  - the staging checks in agent7-s3-proposal.md §(b) still apply (exports are a superset, no amd_fidelityfx import, compile_commands has SDK=1 and no RUNTIME);
  - the §4 hazards should go to the owner as a note.

## 7. Caveats
- **rex_app.cpp:** I read lines 1-140 of 904. The rest is covered by the grep (no paint config, flow or effect uses) and by the exe map (pointer-only imports).
- **Static analysis only:** this rests on source reads and import tables, not a compiled test. A layout bug would show up as wrong config values or heap corruption around presenter objects, and only in xenos mode.
- **Line numbers:** they're from the live tree. If S3 builds from snap1 or snapB, they hold as long as no batch touched `include/rex/ui`, `src/ui` or the SDK CMake files. I know of none.
