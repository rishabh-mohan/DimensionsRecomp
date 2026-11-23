# Task #33 — research-subagent prompts (Agent 9)

These are the three read-only `research` prompts for task #33. They are launched only after Agent 1 sends 'go'. Each prompt is the SHARED block followed by its own part.

## SHARED

You are a read-only research subagent working for Agent 9 on task #33, an Android feasibility report for porting a statically recompiled Xbox 360 game (LEGO Dimensions, PPC to C++ via the rexglue SDK) to two phones:
- Galaxy S25 FE: Exynos 2400, Xclipse 940, 8 GB.
- Rooted OnePlus Nord N30: Snapdragon 695, Adreno 619, 8 GB.

Workspace root: `<workspace>`.

RULES
- Read-only. Write no files. Run no builds, no game, no git writes, and no command that writes anything.
- Keep tool use light. The machine is shared and a timing run may be in progress.
- Never search the whole workspace, and never search `build/` or any `out/` directory. Scope every search to the directories named below.
- Don't read huge generated files in full; read line ranges instead.
- Don't start subagents of your own.

REPO MAP
- SDK: `DimensionsRecomp/rexglue-sdk`
  - `src/core`, `src/ui`, `src/input`, `src/audio`, `src/system`, `src/filesystem`, `src/kernel`
  - `src/graphics`: the rexgpu-xenos plugin, with Vulkan and D3D12 backends
  - `src/codegen`: the PPC-to-C++ recompiler. Its builders are in `src/codegen/builders/*.cpp`.
  - `include/rex`, `resources/templates`, `thirdparty/CMakeLists.txt`, `CMakeLists.txt`, `CMakePresets.json`, `.github/workflows`
- Game: `DimensionsRecomp/rexlego`
  - `CMakeLists.txt`, `src/`
  - `src/gpu_native/`: the opt-in, Windows-only native D3D12 renderer
  - `generated/`: recompiled PPC code
- Tools: `DimensionsRecomp/tools`
- Team notes (read-only, useful for measured numbers): `perf-notes/*.md`

ALREADY ESTABLISHED (cite these if useful; don't re-verify)
- The shipping renderer is the SDK's Xenia-derived rexgpu-xenos plugin, which is runtime-loaded (`src/graphics/CMakeLists.txt:1-5, :101`).
  - Vulkan backend: `src/graphics/CMakeLists.txt:46-57`. SPIR-V translator: `:35-44`. D3D12 backend: `:59-88`, only when `REXGLUE_USE_D3D12` is set.
  - The game's native D3D12 renderer is opt-in and WIN32-only (`rexlego/CMakeLists.txt:19-22, :61-64`). Plume's Vulkan backend is filtered out (`:94-99`).
- Memory ordering: `src/codegen/builders/system.cpp:33-49` emit nothing for sync, lwsync and eieio ("x86 has strong ordering"). `:51-73` (db16cyc, cctpl, cctpm, cctph) are also no-ops.
- Platform macros: `include/rex/platform.h:35-37` defines `REX_PLATFORM_ANDROID=1` and `REX_PLATFORM_LINUX=1` for `__ANDROID__`.
- CMake platform detection (`CMakeLists.txt:174-213`) has no Android branch, so Android falls into linux-arm64. `CMakePresets.json:89-96` is linux-arm64 (`-march=armv8-a`).
- linux-arm64 CI (`.github/workflows/build-linux-aarch64.yaml:3-6`, `_build-platform.yaml:30, :73-126`) only builds and installs, on tags, on `ubuntu-24.04-arm` with clang 20. It runs no tests.
- arm64 support in core:
  - `src/core/memory.cpp:20-22, :205-319`: NEON byte-swap.
  - `src/core/exception_handler_posix.cpp:112-162, :195-251, :396-414`: Linux arm64 signal context, ESR decode and register writeback.
  - `src/system/mmio_handler.cpp:267-359`: arm64 load/store decode. `:50-53` says MMIO itself goes through REX_MM_LOAD/STORE in generated code, and the fault path is for SharedMemory write tracking.
- Android leftovers (from Xenia):
  - `src/core/memory_posix.cpp:48-58, :87-112, :436-458`: ASharedMemory / ashmem instead of shm_open.
  - `src/core/threading_posix.cpp:47-52, :69-94, :107-117`: a kThreadTerminate signal, because there is no pthread_cancel.
  - Both call `rex::GetAndroidApiLevel()`, and threading_posix includes `<rex/main_android.h>`. `include/rex/main_android.h` does NOT exist.
- Paths:
  - `src/core/filesystem_posix.cpp:94-104`: GetExecutablePath reads `/proc/self/exe`, which is app_process64 on Android.
  - `:106-124`: GetUserFolder uses XDG_DATA_HOME, then HOME/.local/share, then passwd.
  - `src/system/gpu_plugin_loader.cpp:57-65`: loads `librexgpu-xenos*.so` from GetExecutableFolder().
- UI and surfaces:
  - `src/ui/CMakeLists.txt:69-82`: SDL3 windowing; non-Windows, non-Apple builds use `surface_gnulinux.cpp`, which is XCB/Wayland only (`src/ui/surface_gnulinux.cpp:21-41`).
  - `src/ui/CMakeLists.txt:152-166`: `pkg_check_modules` for x11-xcb and wayland-client is REQUIRED on UNIX AND NOT APPLE.
  - `thirdparty/CMakeLists.txt:296-307`: forces SDL X11, Wayland, ALSA, Pulse and PipeWire ON for UNIX AND NOT APPLE.
- Link and devices:
  - `src/core/CMakeLists.txt:103-104`: links pthread, rt and dl.
  - libusb and the physical portal are Windows-only (`thirdparty/CMakeLists.txt:711-737`; `src/input/CMakeLists.txt:34-46`).
  - The emulated Toy Pad (`src/input/portal/emulated_toypad.cpp`) builds everywhere.
  - Audio is SDL plus FFmpeg XMA decode (`src/audio/CMakeLists.txt`). FFmpeg has aarch64 NEON config (`thirdparty/CMakeLists.txt:447-454, :547-559, :669-686`).
- Clocks and threads:
  - `src/core/clock_posix.cpp` uses CLOCK_MONOTONIC_RAW, with no rdtsc.
  - `src/core/threading_posix.cpp:176`: EnableAffinityConfiguration is an empty TODO.

OUTPUT
Reply with markdown only, and write no files. Use these sections:
1. Findings: each with `path:line`.
2. Blockers: things that must be fixed before an Android arm64 build, first run or first frame.
3. Easy items.
4. Effort guesses: in person-days or person-weeks, as a range.
5. Unknowns, and what would resolve them.

Keep it to about 1500 words. Give `path:line` for every repo claim, and mark anything not seen in the repo as "unverified".

## (a) SDK

Investigate the SDK side. Use path:line for each point.

1. Generated-code headers.
   - Find what the generated C++ includes: look at the first ~40 lines of two files in `DimensionsRecomp/rexlego/generated/`, then follow the includes into `include/rex/ppc/*.h` and any recompiler runtime headers.
   - List every x86-only construct there and in `src/codegen/builders/*.cpp` and `resources/templates`: raw `_mm_*`/`__m128` not via SIMDe, `__rdtsc`, `_mm_pause`, `__builtin_ia32_*`, inline asm, `immintrin.h`/`x86intrin.h`, `_mm_getcsr`/`_mm_setcsr`/MXCSR, `_MM_SET_FLUSH_ZERO_MODE`/`_MM_SET_DENORMALS_ZERO_MODE`, and `__cpuid`.
   - How are these implemented: mftb/mftbu (time base), lwarx/ldarx/stwcx./stdcx. (reservations; atomic type and memory order), and the FPSCR rounding mode and VMX non-Java/denormal mode?
2. Memory ordering on arm64.
   - Apart from `system.cpp:33-49`, is there any ordering at all? For example: do guest loads and stores emit plain non-atomic accesses, and are reservations seq_cst CAS?
   - Propose what an arm64 codegen option should emit for sync, lwsync, eieio and isync (e.g. `std::atomic_thread_fence` seq_cst / acq_rel / release, or `__dmb`), and what to do about volatile MMIO and GPU ring-buffer writes.
   - Estimate the cost: how many sync/lwsync/eieio sites are in the generated code? Count with a search scoped to `rexlego/generated`.
3. Guest memory.
   - In `src/system/xmemory.cpp` and its headers: the fixed host addresses of the virtual and physical membase (see `CMakeLists.txt:262-268`: "custom mmap at 0x100000000"), the number of views, and the total reserved VA.
   - Host-page-size assumptions: what happens with a 16 KB host page (macOS arm64 is 16 KB; see the comment at `memory_posix.cpp:261-264`), and what is the granularity of the physical write watch?
   - Will the VA layout fit a 39-bit arm64 Android user VA (512 GB)?
4. Android leftovers. List every `REX_PLATFORM_ANDROID` / `__ANDROID__` site in the SDK's `src/` and `include/`, with a one-line status for each. Confirm whether `GetAndroidApiLevel` or `main_android` exists anywhere in the SDK.
5. Vulkan.
   - In `src/ui/vulkan/` (instance, provider, device, presenter) and `src/graphics/vulkan/`: which instance and device extensions and features are required and which are optional?
   - Is VK_KHR_android_surface handled? What Surface types exist (`include/rex/ui/surface*.h`)?
   - What happens without each of these: textureCompressionBC, geometryShader, fillModeNonSolid, independentBlend, shaderStorageImageWriteWithoutFormat, fragmentStoresAndAtomics, vertexPipelineStoresAndAtomics, shaderClipDistance, depthClamp, samplerAnisotropy, imageCubeArray, fragmentShaderSampleInterlock.
   - Is there a BC/DXT decompression fallback, and does the render-target cache have a non-FSI path?
   - Minimum Vulkan API version.
6. SDL3 and the window handle.
   - How does `window_sdl.cpp` / `windowed_app_context_sdl.cpp` get the native handle for the surface (SDL window properties)? Does an Android path exist?
   - Where does `vulkan/api.h` pull in `<wayland-client.h>` (`src/ui/CMakeLists.txt:155-157`)?
   - Can the entry point become an SDL3 Android SDL_main .so?
7. bionic gaps. Check each of these in `src/core/*_posix.cpp`:
   - `src/core/fiber_posix.cpp`: does it use ucontext (getcontext/makecontext/swapcontext don't exist in bionic)?
   - `backtrace()` / `execinfo.h` (API 33+ only).
   - `pthread_cancel` (absent).
   - `shm_open` (absent).
   - `memfd_create` (API 30+).
   - `timer_create` with SIGEV_THREAD_ID.
   - `pthread_setaffinity_np`.
   - `posix_spawn`.
   - Also in `src/core/dbg_posix.cpp`, `socket_posix.cpp` and `system_posix.cpp`: any glibc-only calls.
8. Paths: list every `GetExecutableFolder`/`GetExecutablePath`/`GetUserFolder` call site in the SDK `src/`.
9. Threads: thread priority and affinity setters in `threading_posix.cpp` (SCHED_FIFO/RR? nice?), and the typical set of host threads: guest threads 1:1, GPU command processor, audio/XMA, timer queue and so on.
10. Effort ranges for three milestones:
    - (i) The SDK compiles and links for arm64-android (API 26+, NDK r27+ clang 18+); no run.
    - (ii) Headless boot to the guest entry point.
    - (iii) The Vulkan presenter shows the first frame.

## (b) Game

Investigate the game side (`DimensionsRecomp/rexlego` plus how it uses the SDK). Use path:line for each point.

1. `rexlego/CMakeLists.txt` (~800 lines): list every WIN32-only or Windows-specific piece and what a non-Windows configure does today.
   - Known pieces: `:8-12` RC; `:61-64` native GPU FATAL off Windows; `:77-99` Plume D3D12-only; `:143-148` TT lock trace; `:168-179` add_executable and /MAP; `:181-200` DXIL shader banks; `:775-800` native fingerprint.
   - Which options gate native GPU, and what are their defaults? Can a Linux/Android configure turn ALL of it off cleanly?
2. `src/gpu_native/`: raw D3D12 (d3d12.h, ID3D12*) vs Plume (plume::*) use. Count files of each kind.
   - Are the `src/native_*.cpp` hooks compiled and active when native GPU is off?
   - Beyond Plume, what is inherently D3D12 (DXIL banks, root signatures, enhanced barriers, DirectStorage...)?
   - Would Plume's Vulkan backend make it portable in principle?
3. The shipping path: how does `main.cpp` pick the GPU plugin and backend (rexgpu-xenos with d3d12 or vulkan)? Is there a cvar or toml for the backend?
   - Has the D3D12 backend got game-specific fixes or features the Vulkan backend lacks? Search `rexglue-sdk/src/graphics/d3d12/` vs `src/graphics/vulkan/` for LEGO/Dimensions/2026-dated comments and cvars, and list D3D12-only fixes the game relies on.
   - Do recent perf notes (`perf-notes/`) say whether the Vulkan backend has been run for this game at all?
4. Toy Pad.
   - `src/toypad_app.cpp`; SDK `src/input/portal/{portal.cpp, emulated_toypad.cpp, hardware_portal.cpp}`.
   - What does the emulated Toy Pad need (loopback listener per `src/input/CMakeLists.txt:42-46`, UI)?
   - What are the USB VID/PID, interfaces, endpoints and transfer types in `hardware_portal.cpp`?
   - What would Android need: UsbManager permission plus `libusb_wrap_sys_device`, or SDL hidapi, or Java USB with JNI?
5. Windows-only APIs in game sources (exclude `gpu_native/`): grep `rexlego/src` for `windows.h`, Win32 calls (MessageBox, CreateFile, QueryPerformanceCounter, SetUnhandledExceptionFilter, MiniDumpWriteDump, WinHTTP/WinINet, ShellExecute, the registry, COM, DXGI, timeBeginPeriod), and `_WIN32` guards.
   - For each file, give one row: portable / guarded / needs a port, with path:line.
   - Files include main.cpp, crash_guards.cpp, crash_popup.cpp, discord_presence.cpp, updates.cpp, sample_profiler.cpp, settings_*.cpp, toypad_app.cpp and native_effects.cpp.
6. Audio and input: does the game add anything beyond the SDK's SDL audio and input (XInput-only paths, keyboard mapping, rumble)?
7. File I/O and content.
   - Where does the user's own game content (XEX and data) live at runtime: a content-root option, or a path relative to the exe?
   - Where do saves, config and shader/pipeline caches go?
   - Case sensitivity: Xbox paths are case-insensitive. Does the SDK VFS (`rexglue-sdk/src/filesystem`) do case-insensitive host lookup?
8. Generated code, scoped ONLY to `rexlego/generated/`.
   - Count the files and their total size.
   - Search for `__rdtsc`, `_mm_pause`, `__builtin_ia32`, `asm(`/`__asm__`, `immintrin`, `x86intrin`, and raw `_mm_` not prefixed with simde. Give counts and one example path:line for each.
   - Note the header(s) every generated file includes.
9. Effort ranges for: (i) the game target configures and compiles on Linux/Android with native GPU off; (ii) the game-specific Windows-isms are ported or stubbed.

## (c) Android (repo side and devices)

Investigate the Android-specific side. Use path:line for repo claims, and mark device facts "unverified" unless confirmed by a source (search_web, if your tools have it; cite URLs).

1. Measured footprint, from `perf-notes/*.md` only (read-only):
   - exe/DLL sizes, working set/RSS, VRAM, number of host threads, the hot threads and their CPU share, and desktop frame time/FPS.
   - The desktop CPU and GPU model these were measured on.
   - From these, estimate the CPU headroom needed on a phone.
2. Spin and busy-wait behaviour. These matter for thermals.
   - From perf-notes (search for GPU-wait back-off, db16cyc/pause, spin, yield) and the SDK (`threading_posix.cpp` MaybeYield/SyncMemory; command-processor waits in `src/graphics/command_processor.cpp`): list the known spin loops and their status.
3. Controllers: `src/input/sdl/sdl_input_driver.cpp`. Does it use the SDL3 gamepad API, so Android gamepads (Bluetooth or USB) map automatically? Touch controls: is there anything at all?
4. Storage and game files.
   - What format does the user's own game dump take: an extracted folder, ISO, or GOD? How big is it? Check `DimensionsRecomp/README*`, `rexlego/README*`, `docs/` if present, and perf-notes.
   - Where would it go on Android, given the path code above? Options: app-specific external storage (`Android/data/<pkg>/files`, reachable over MTP), MANAGE_EXTERNAL_STORAGE for a sideloaded app, or SAF (no POSIX paths).
5. Toy Pad over USB-OTG. Use the protocol details in `rexglue-sdk/src/input/portal/hardware_portal.cpp` (VID/PID, endpoints, report size, timing).
   - Feasibility via the Android USB host API (permission dialog, then a file descriptor, then `libusb_wrap_sys_device`).
   - Feasibility via root on the N30 (direct /dev/bus/usb).
   - Power: does the portal draw power within OTG limits? Unverified unless documented.
6. Device facts. Use search_web if available; otherwise give your knowledge, marked unverified. For each phone:
   - CPU clusters and clocks.
   - GPU, Vulkan version and driver. On the N30, can Mesa Turnip be used (adrenotools or root)?
   - Native BCn texture support.
   - geometryShader support.
   - RAM available to one app.
   - Kernel page size (4 KB vs 16 KB).
   - Android version.
   - Sustained-performance and thermal behaviour.
   - Any Xenia-on-Android / Vulkan Xbox 360 emulation evidence (e.g. "Xenia Android", "aX360e" / "X360 Mobile") showing these GPUs can run the Xenos-emulation shaders.
7. Phone roles. Compare a phone CPU with the desktop CPU: rough single-thread ratio (GB6 single-core class numbers, unverified) and core counts. What is each phone realistically good for (target vs dev/test), and what fps class is plausible?
8. Effort ranges for the APK shell, input, storage, the OTG Toy Pad, and performance/thermal tuning.
