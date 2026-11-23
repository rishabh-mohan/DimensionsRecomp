# Agent 6 / subagent B: injected with -DCMAKE_PROJECT_INCLUDE=<this file>.
# CMake includes this file as the last step of every project() call. See ffx_project_before.cmake.
# It restores CMAKE_GENERATOR_PLATFORM as a NORMAL variable in the sdk scope, which
# libs/pix/CMakeLists.txt needs. It is never written to the cache, so a re-configure with Ninja
# keeps working.
if(DEFINED _FFXB_SAVED_GENERATOR_PLATFORM AND NOT DEFINED CMAKE_GENERATOR_PLATFORM)
  set(CMAKE_GENERATOR_PLATFORM "${_FFXB_SAVED_GENERATOR_PLATFORM}")
  message(STATUS "[agent6-B] restored CMAKE_GENERATOR_PLATFORM='${CMAKE_GENERATOR_PLATFORM}' (normal variable) after project()")
endif()
