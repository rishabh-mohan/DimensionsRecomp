# #33 Android feasibility: working state (Agent 9)

Saved 17:08, just before the agy-grid restart. Resume from here.

## Where I am

- 'go' is NOT received yet.
  - Before 'go': file tools only.
  - After 'go': up to 3 `research` subagents, read-only, one per part. Each prompt is SHARED plus its part from prompts.md, pasted inline, plus the extra asks below.
- Hold rule: no tool calls at all while perf-notes/WINDOW-HOLD.txt exists.
- perf-notes/ANDROID-FEASIBILITY.md is still the v0 skeleton.
- Next steps:
  1. Write v1 from the findings below.
  2. Merge the subagent results.
  3. Reply `@@done 33: <path + 5-line summary>`.

## Extra asks for the subagents (not yet in prompts.md)

- (a)
  - Who uses rex::thread::Fiber.
  - Count the `// sync`, `// lwsync`, `// eieio` and `// isync` comment sites in GAME/generated/default/*.cpp.
  - How lwarx/stwcx/isync are emitted (memory builder).
  - Whether src/ui/vulkan/vulkan_presenter.cpp creates an Android surface.
  - How FP control (MXCSR/FPSCR/VSCR) is handled, and what it maps to on arm64.
  - The Vulkan features the backend requires.
- (b)
  - Sweep GAME/src for unguarded Windows APIs: does the game build on Linux today?
  - Raw D3D12 vs Plume use in src/gpu_native.
  - Where the content path comes from.

## New findings this session (all read by me)

### SDK build

- SDK CMakeLists.txt:
  - :37-39: REXGLUE_USE_VULKAN is an option on Windows, OFF by default. **So the Vulkan backend can be tried on the user's desktop first** (plan P0a).
  - :149-161: non-x86 gets `-mcmodel=small`, and PIC is ON for every non-Windows target. Both are fine for a JNI .so.
  - :193-201: Android counts as UNIX AND NOT APPLE, so it lands in REX_PLATFORM=linux-arm64 with REX_PLATFORM_LINUX=1. :211-212 FATAL is not reached.
- system.cpp:
  - :33-49: sync/lwsync/eieio are confirmed as no-ops.
  - :51-73: db16cyc and cctpl/m/h are no-ops.

### SDK sources

- src/graphics/CMakeLists.txt:
  - :1-5, :101: rexgpu-xenos is a SHARED, runtime-loaded plugin.
  - :35-44: SPIR-V sources.
  - :46-57: Vulkan sources.
  - :90-92: appended under REXGLUE_USE_VULKAN.
- src/ui/CMakeLists.txt:
  - :37-53: the Vulkan UI sources, including vulkan_presenter.cpp and vulkan_moltenvk.cpp.
  - :69-82: the platform surface; anything that isn't Windows or Apple gets surface_gnulinux.cpp.
  - :152-166: x11-xcb and wayland-client are REQUIRED.
- src/input/CMakeLists.txt:
  - :4-12: emulated_toypad builds everywhere.
  - :34-39: sdl_input_driver is on every platform; xinput and hardware_portal are WIN32-only.
  - :42-46: ws2_32 and libusb are WIN32-only.
- src/input/portal/emulated_toypad.cpp:
  - :37-41, :51-55, :72-77: POSIX socket paths exist.
  - :59-63: a loopback listener that the companion app polls.
  - :80-85: the picker handoff uses a Windows named event.

### GAME

- GAME/CMakeLists.txt:
  - :25-59: the always-built sources.
  - :61-64: native GPU is FATAL off Windows.
  - :77-99: Plume, with its Vulkan backend filtered out at :94-99.
  - :168-173: there is a non-WIN32 add_executable.
- sample_profiler.cpp:21 and :326: the whole file is `#if defined(_WIN32)`.
- toypad_app.cpp:
  - :3-5: the companion app owns the loopback listener.
  - :102-198: Windows-only.
  - :204-222: Launch logs a warning off Windows (:219-221).
  - :131-136: closing the window hard-exits with std::_Exit(0) (ReXApp::OnClosing). This is a lifecycle gap on Android.
- updates.cpp:
  - :21-23: Windows guard.
  - :44-50: rexupdate.exe.
  - :52-70: CreateProcessW.
- discord_presence.cpp:
  - :3-11: named-pipe IPC.
  - :36-40: windows.h guard.
- Native hooks (plain C++ and portable, but tuned only on x86-TSO):
  - native_atomics.cpp:35-49: atomic_ref and bswap.
  - native_memops.cpp:29-40: the 0xE0000000 +0x1000 view rule. :62-78: memset.
  - native_lock_elide.cpp:1-2: generated, with the global lock removed. :40-46: the LEGO_NATIVE_LOCK_ELIDE env var, default on. :49: ppc_global_lock_count_.
  - crash_guards.cpp: guarded hooks.
  - On arm64, start with LEGO_NATIVE_LOCK_ELIDE=0 and re-validate.

## Plan draft (person-weeks)

| Phase | Work | Effort |
|---|---|---|
| P0a | Desktop Windows build with REXGLUE_USE_VULKAN=ON; does rexgpu-xenos Vulkan draw the game? | 0.5-2 |
| P0b | arm64 fence codegen option (default OFF, byte-identical when OFF), arm64 regen, NDK compile of objects | 1-2 |
| P1 | linux-arm64 bring-up in a chroot on the rooted N30 (or any arm64 Linux box): boot to title, attract loop | 2-4 |
| P2 | Android build target: toolchain, CMake/SDL3/rexui Android branches, main_android, fibers, plugin path, file paths; headless adb run | 2-4 |
| P3 | APK shell: SDLActivity, JNI paths, ANativeWindow surface, lifecycle | 2-3 |
| P4 | Mobile Vulkan on Xclipse/Adreno: features, drivers, BC, pipeline cache, memory | 3-8 |
| P5 | Input, storage and Toy Pad: in-app picker, optional OTG | 2-6 |
| P6 | Performance and thermals: pinning, ADPF, resolution scale, pacing | 3-8 |

- Total: ≈16-37 person-weeks.
- Gates:
  - After P0a: the Vulkan path works.
  - After P1: arm64 plus fences is stable.
  - After P4's first frames: the fps class.
