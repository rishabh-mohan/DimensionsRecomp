# FFX option A: fsyntax of rexui with the FidelityFX SDK headers (M2, S5 item 2)

**Result: PASS.** All 36 Release rexui compile entries pass `-fsyntax-only` with `REX_HAS_FIDELITYFX_SDK=1` (35 TUs + PCH; 0 failed). No bin was built, nothing was installed, and no repo was touched.

## How
- **Script:** `s5/ffx-a/run-ffx-a.py`. Rerun with `--reuse`.
- **Configure:** a new configure dir, `s5/ffx-a/b`.
  - VS CMake 3.28 `--preset win-amd64`, with cwd = the snap1 SDK source.
  - `-DREXGLUE_FIDELITYFX_SOURCE_DIR=<snap1>/rexglue-sdk/thirdparty/FidelityFX-SDK`. It has sdk/include and ffx-api/include but is not a git checkout.
  - The install prefix is `install-never`; nothing is installed.
- **fsyntax:** the PCH is replaced by a textual `-include`, run at -j4, idle priority.
- **Logs:** `configure.log`, `fsyntax.log`, `ffx-a-check.txt` and `src-compare.txt`.

## Checks (`ffx-a-check.txt`, RESULT PASS)
- **CMakeCache matches snap1-sdk** except for:
  - the install prefix;
  - the FFX source dir;
  - the C/CXX compiler spelling (bare name vs full path; it is the same compiler in the ccdb);
  - CMAKE_RC_COMPILER (llvm-rc vs rc.exe, from PATH order; rexui has no .rc files).
- **ccdb:**
  - 2277 entries, the same count as snap1-sdk.
  - `-DREX_HAS_FIDELITYFX_SDK=1` is on exactly the 108 rexui entries, 36 of them Release.
  - Every non-rexui command is identical to snap1-sdk's, apart from the build dir. The earlier "27 differ" was a script bug in the PCH-entry key (backslash and case forms of the build dir); it is fixed.
- **Sources** (`src-compare.txt`): snap1 vs a7e79c0 has 961 files the same and 13 different. None of the 13 is in `src/ui` or `include/rex/ui`, so the rexui result holds for a7e79c0.

## ODR notes (the define is PRIVATE to rexui, `src/ui/CMakeLists.txt`)
These match `perf-notes/agent7-odr-ffx.md`, re-checked by grep at a7e79c0.
- **Guarded headers:**
  - `include/rex/ui/presenter.h` (12 guards);
  - `d3d12/d3d12_presenter.h` (2 guards);
  - `vulkan/presenter.h` (2 guards; Vulkan is not compiled here).
- **What changes layout:**
  - `GuestOutputPaintConfig` grows from 12 B to 28 B (presenter.h:317-322), so every `Presenter` member after `guest_output_paint_config_` (presenter.h:938) shifts by 16 B.
  - `GuestOutputPaintEffect::kCount` changes (:430-438), and so does `kMaxGuestOutputPaintEffects` (:473ff), which changes `GuestOutputPaintFlow`.
  - D3D12Presenter: the root-signature index count goes from 1 to 5 (d3d12_presenter.h:133-143), which changes its arrays and `PaintContext`.
  - No virtual function is guarded, so the vtables are the same.
- **Non-rexui includers (compiled without the define):**
  - headers: `graphics/command_processor.h`, `graphics_system.h`, `ui/window.h`, `graphics_provider.h`, `imgui_drawer.h`, `immediate_drawer.h`;
  - `src/graphics/d3d12/command_processor.cpp` (rexgpu-xenos.dll), which only uses `D3D12GuestOutputRefreshContext` (unguarded) and static DXGI constants;
  - rexlego has no use of GuestOutputPaint*/Presenter types (grep of the superproject HEAD).
- **Verdict:** this is a formal ODR violation, but it is benign in practice. No user outside rexui touches a layout-dependent member, constructs Presenter, or takes its sizeof. Latent hazards:
  - (6) COMDAT: inline functions with guard-dependent bodies (`CanGuestOutputPaintEffectBeIntermediate/Final`, `GetGuestOutputPaintRootSignatureIndex`) could be folded across TUs. Today only rexui TUs instantiate them.
  - (7) LTO: cross-TU inlining could mix the two layouts.
  - Any future inline Presenter accessor used outside rexui would read wrong offsets.
- **Next step, if a bin is wanted:**
  - build rexui (36 TUs) with the define;
  - relink rexruntime.dll only;
  - pe-check exports;
  - do a needle check for the FFX paths.

  The FFX runtime libs (`REX_HAS_FIDELITYFX_RUNTIME`) are not part of option A.
