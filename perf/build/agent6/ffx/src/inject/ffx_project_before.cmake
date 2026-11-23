# Agent 6 / subagent B: injected with -DCMAKE_PROJECT_INCLUDE_BEFORE=<this file>.
# CMake includes this file as the first step of every project() call.
#
# Why it exists: the copied FidelityFX sdk/CMakeLists.txt includes toolchain.cmake BEFORE its first
# (and only) project() call, and toolchain.cmake was written for the Visual Studio generators:
#  * It force-caches CMAKE_GENERATOR_PLATFORM=x64. The single-config Ninja generator rejects any
#    platform when the first project() enables languages ("Generator Ninja does not support platform
#    specification"). So the value is hidden while languages are enabled, and
#    ffx_project_after.cmake puts it back as a normal (never cached) variable.
#    sdk/CMakeLists.txt already used it before project() to set FFX_PLATFORM_NAME=x64, and
#    libs/pix/CMakeLists.txt needs it for bin/x64/WinPixEventRuntime.{lib,dll}.
#  * It sets CMAKE_SYSTEM_NAME=WINDOWS and CMAKE_SYSTEM_VERSION=10.0 as normal variables before
#    project(). CMakeDetermineSystem would then treat the build as cross-compiling. Dropping them
#    lets CMake detect the Windows host natively, the same way the game and rexglue builds do.
#
# This is equivalent to what upstream ffx-api (and rexglue_fidelityfx.cmake) get by calling project()
# first and then add_subdirectory(../sdk), followed by unset(CMAKE_GENERATOR_PLATFORM CACHE).
# Doing it this way means no CMakeLists.txt has to be written or edited.
if(NOT CMAKE_SYSTEM_LOADED)
  if(DEFINED CACHE{CMAKE_GENERATOR_PLATFORM})
    set(_FFXB_SAVED_GENERATOR_PLATFORM "$CACHE{CMAKE_GENERATOR_PLATFORM}")
    unset(CMAKE_GENERATOR_PLATFORM CACHE)
  endif()
  unset(CMAKE_GENERATOR_PLATFORM)
  unset(CMAKE_SYSTEM_NAME)
  unset(CMAKE_SYSTEM_VERSION)
  message(STATUS "[agent6-B] hid CMAKE_GENERATOR_PLATFORM='${_FFXB_SAVED_GENERATOR_PLATFORM}' and the toolchain.cmake system preset for language enablement")
endif()
