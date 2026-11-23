// Force-included (clang++ -include) into discord_presence.cpp for the bench
// build ONLY. Discord is running on the bench machine, so \\.\pipe\discord-ipc-0
// exists and the presence thread would really connect to it. This routes the
// source's CreateFileA to bench_CreateFileA (defined in bench_discord.cpp),
// which renames \\.\pipe\discord-ipc-N to a pipe that does not exist (the same
// failing kernel call a machine without Discord makes) and refuses anything
// else. The source's own later #include <windows.h> is a no-op (include
// guard), so its code is compiled unchanged otherwise.
//
// build-runtime-benches.ps1 checks with llvm-nm that the discord objects
// reference bench_CreateFileA and not __imp_CreateFileA before linking.
#pragma once

#include <windows.h>

extern "C" HANDLE WINAPI bench_CreateFileA(LPCSTR name, DWORD access, DWORD share,
                                           LPSECURITY_ATTRIBUTES security, DWORD disposition,
                                           DWORD flags, HANDLE template_file);

#undef CreateFileA
#define CreateFileA bench_CreateFileA
