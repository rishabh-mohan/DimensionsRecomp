# Agent 9 working notes: Android feasibility (task #8, was #33)

Session 2, started 19:31 on 2026-11-22. Read-only study. These are my own reads. The subagent reports are saved next to this file as subagent-a.md, subagent-b.md and subagent-c.md when they arrive.

## Checked by me (path:line)

- SDK `src/codegen/builders/system.cpp:33-49`: `build_sync`, `build_lwsync` and `build_eieio` each return true and emit nothing. The comments say "x86 has strong ordering so this is a no-op". Lines 21-73 do the same for nop, attn, db16cyc and cctpl/m/h (harmless).
- GAME `CMakeLists.txt:19-22`: `LEGODIMENSIONS_NATIVE_GPU` ("experimental native D3D12 renderer") is OFF by default. The shipping path is "rexgpu-xenos", the SDK's Xenos GPU emulation.
- GAME `CMakeLists.txt:61-64`: when the native GPU is on and the target isn't WIN32, configure fails with "currently supports Windows D3D12 only".
- GAME `CMakeLists.txt:89-99`: the native path uses Plume (`thirdparty/plume`), but strips `plume_vulkan.(cpp|h)` from the plume target on purpose ("This build is deliberately D3D12-only").
- GAME `CMakeLists.txt:233`: links `plume d3d12 dxgi`. Lines 236-248: FSR3 through prebuilt `ffx_backend_dx12_x64.lib`, `ffx_fsr3upscaler_x64.lib` and `amd_fidelityfx_dx12.dll` (x64 and DX12 only).
- GAME `CMakeLists.txt:264-273, 310-321, 353-380, 566-577`: the shader banks are DXIL from DXC (XenosRecomp output plus host HLSL at SM 6.0). There is no SPIR-V anywhere in this path.
- GAME `CMakeLists.txt:603`: the fingerprint list names `tools/gpu-aot/patches/plume-vulkan-readback.patch`, so someone has touched Plume's Vulkan side.
- GAME `CMakeLists.txt:8-12, 168-173`: non-WIN32 project and executable branches exist. Line 147: the TT lock trace is Windows-only (thread CPU clocks).
- GAME `CMakeLists.txt:319-321, 444-452`: the native path already handles Windows-on-ARM64 (DXC arm64, clang-cl ARM64 COFF).
- GAME `CMakeLists.txt:823-857`: `-march=x86-64-v3` and `-O3` are applied only when `CMAKE_SYSTEM_PROCESSOR` matches x86_64, so an arm64 build is not broken by them. Lines 835-839 say the SDK byte-swap helpers need SSSE3 and that `REXGLUE_X86_BASELINE` must match.
- GAME `CMakeLists.txt:862-885`: ThinLTO is an option; it's capped at 2 jobs to fit 16 GB.
- GAME `generated/rexglue.cmake:38-47`: "Guest SEH scopes emit __try/__except". `/EHa` or `-fasync-exceptions` is added only `if(WIN32)`. Clang targeting Android has no SEH, so check how the scopes are emitted.
- GAME `generated/rexglue.cmake:111-123`: `REXGLUE_HOST_CODEGEN_EXECUTABLE` lets a cross build run a host-native codegen CLI, which fits an NDK cross build from Windows.
- GAME `generated/rexglue.cmake:78-109`: the generated code is an OBJECT library `<target>_recomp` with a PCH (`legodimensions_pch.h`).

## Device facts (web search, 19:34-19:36; treat as secondary sources)

- S25 FE: Exynos 2400 (4 nm). CPU 1x X4 at 3.21 GHz, 2x A720 at 2.9 GHz, 3x A720 at 2.6 GHz, 4x A520 at 1.95 GHz. Xclipse 940 (RDNA3), Vulkan 1.3. Vapor chamber. CPU clocks drop after about 10 minutes of stress, and the GPU loop stability can fall below 50% (GSMArena summary). GB6 single-core about 2100-2200.
- Nord N30 5G: SD695 (6 nm). CPU 2x A78 at 2.2 GHz, 6x A55 at 1.7 GHz. Adreno 619 (a6xx gen1). 8 GB LPDDR4X, 128 GB UFS 2.2, microSD. Shipped with Android 13; the policy is one OS update (Android 14). GB6 single-core about 900.
- Adreno 619: the stock driver is Vulkan 1.1 (some builds 1.2). Mesa Turnip supports a6xx, including a619, up to Vulkan 1.3. Loading Turnip is per-app via adrenotools, or system-wide with root.
- Xclipse: Turnip doesn't apply, so you're stuck with Samsung's stock driver. Emulator community reports show more driver trouble there than on Adreno with Turnip. (These are low-quality sources and only signal a risk.)
- 16 KB pages: since 2025-11-01, Play requires apps that target API 35+ and carry native code to support 16 KB pages. NDK r27+ supports this (link with `-z max-page-size=16384`). A sideloaded APK on a 4 KB-kernel phone isn't affected, but the runtime should still not assume 4 KB.

## Subagent reports (session 2)

If this session dies, the full reports are in the subagent transcripts:
- (a) SDK: conversation b7bb3cb3-73e0-43ad-a67b-d20108ef54dd, `C:\Users\<user>\.gemini\antigravity-cli\brain\b7bb3cb3-73e0-43ad-a67b-d20108ef54dd\.system_generated\logs\transcript.jsonl`
- (b) GAME: conversation 2dcbe759-de3f-49bf-a3b0-2012235a9a5f. Report received 19:50.
- (c) Android: conversation 811634b9-61e7-49cd-8245-b377d4f61b5c

Key points from (b), all cited path:line in the report:
- Shipping build: the xenos plugin. `rex_app.cpp:61-69` defines the `gpu_backend` cvar (any/d3d12/vulkan). `SDK/CMakeLists.txt:34-47` turns D3D12 off and Vulkan on for non-Windows builds.
- The project calls its own Vulkan path unstable and a fallback only (`ui_theme.cpp:193-196`, `README.md:302-325`), and the perf builds don't even compile it (`REXGLUE_USE_VULKAN=OFF`).
- Native renderer: `device.cpp:343-346` returns nullptr for kVulkan. The DXIL/COFF banks and the FidelityFX DX12 libraries are Windows-only.
- Toy Pad: the emulated pad listens on TCP 9191 and is fed by the LegoToypad.exe companion app. The libusb hardware portal is built on WIN32 only.
- Audio: SDL3 plus FFmpeg XMA, portable. Input: SDL3 is the default; there's no touch driver.
- Content: about 9 GB (base + TU23), about 24 GB with all DLC (`README.md:456-460`).
- Compile blocker: `updates.cpp:198` calls `_wcsnicmp` unguarded.
- Silent bug: `native_memops.cpp:31` hard-codes the 0x1000 offset, but `REX_PHYS_HOST_OFFSET` is 0 on Linux/Android (`legodimensions_pch.h:119-123`).
- Linux arm64 CMake presets exist (`R/CMakePresets.json:61-68, 134-150`). The SDK passes `-march=armv8-a` on aarch64.
- SEH: off Windows, the macros use a SehGuard plus C++ try/catch (`SDK/include/rex/platform/exceptions.h:97-149`).
- Generated code: 886 files, 490 MB (440 .cpp).

## Report (c) Android digest (subagent 811634b9, received about 19:55)
- **Scaffolding:** we have none of our own. Vendored: SDK/thirdparty/sdl3/android-project (SDLActivity, HIDDeviceManager) and SDK/thirdparty/libusb/android/jni. The SDL3 submodule tracks release-3.4.x, but the checkout is a 3.5.0 prerelease: pin it.
- **SEH is not a blocker:**
  - it is emitted as macros (function_graph.cpp:700-727), and only when generateExceptionHandlers is set, which defaults to false (include/rex/codegen/config.h:102);
  - a 12-TU sample had 0 SEH_TRY;
  - seh_posix.cpp:34-74 throws from a signal handler, which is unreliable.
- **jthread:** std::jthread (timer_queue.cpp:226,238) needs libc++ >=18, so NDK r27+.
- **Build cost:** 7,680 CPU-s (perf-notes/agent2-baseline.md:730), about 13 min at -j10. Expect about 35-55 min at -j4.
- **APK shell (use SDLActivity):**
  - windowed_app_main_sdl.cpp:127-131 is a plain main() with no SDL_main.
  - windowed_app_context_sdl.cpp:99-181 ignores the background, foreground, low-memory and terminating events.
  - window_sdl.cpp:385-433 handles HWND, Metal, Wayland and XCB only; it needs an SDL_PROP_WINDOW_ANDROID_WINDOW_POINTER branch.
  - rex_app.h:291-295 provides SetGuestPaused.
  - vulkan_presenter.cpp:799-808 has vkCreateAndroidSurfaceKHR, but surface_android.h is missing.
- **Storage:** all roots are cvars (rex_app.cpp:227-262), but the TOML and logs are exe-dir relative (:210-225, :288-291). GAME exe-relative paths: mod_menu.cpp, ui_theme.cpp:423, updates.cpp. Recommended: /sdcard/Android/data/<pkg>/files/game over MTP, or MANAGE_EXTERNAL_STORAGE when sideloaded. SAF doesn't fit the VFS.
- **Controllers:** the SDL3 gamepad API works as-is. Finger events are filtered out (sdl_input_driver.cpp:77).
- **OTG Toy Pad:**
  - Route A: libusb_wrap_sys_device plus LIBUSB_OPTION_NO_DEVICE_DISCOVERY, with the fd from UsbManager.
  - Route B: SDL hidapi; HIDDeviceManager accepts the 0x0e6f and 0x24c6 vendors.
  - Transfers are 32-byte interrupt, 100 ms.
- **Threads:** about 20 guest pthreads on 6 fake CPUs; ignore_thread_affinities defaults to true. SCHED_FIFO (threading_posix.cpp:852-861) gives EPERM. CpuRelax is yield on non-x86 (xboxkrnl_rtl.cpp:412-418). TimerQueue spins (timer_queue.cpp:29-100). AlertableSleep polls in 1 ms slices.
- **Per-core speed** vs a Golden Cove core at 1.9 GHz: X4 about 1.5-2x, A720 1.0-1.3x, A78 at 2.2 GHz 0.8-1.0x, A55 about 0.3x. The S25 FE can reach 60 fps on CPU until it throttles and can sustain 30. The SD695 is borderline at 30.
- **Estimates:** c1 4-8 d, c2 5-12, c3 5-10, c4 2-5, c5 1-3 (+5-10 for touch), c6 3-6 (+2-4 for the picker), c7 4-8. Total about 29-59 d.
