# LEGO Dimensions Recompiled: optimisation sprint, shared brief

Every worker reads this before starting. The orchestrator (Agent 1) maintains it.

## What we are optimising

- **Project:** *Dimensions Recompiled*, a static recompilation of the Xbox 360 LEGO Dimensions
  (PowerPC to C++ through the ReXGlue SDK). Upstream: https://github.com/NeverCookFirst/DimensionsRecomp
  (archived by its author after the final release, "Native GPU 0.2.0").
- **Game repo:** `games/lego-dimensions-recomp/DimensionsRecomp`, branch `perf/opt`, created from tag
  `v0.2.0`, the final Native GPU D3D12 release. Paths below are relative to this folder unless noted.
  - `rexlego/src/`: game-specific runtime code (settings, mods, native CPU replacements, crash guards).
  - `rexlego/src/gpu_native/`: the **native D3D12 renderer**. It hooks the title's D3D calls and
    renders them directly. It does not emulate the Xenos command buffer. This is the 0.2.0 render path.
  - `tools/gpu-aot/`: about 300 test and benchmark fixtures plus engineering notes. Worth reading:
    `native-performance-20261001.md`, `native-performance-vsync-20261010.md`, `ENGINEERING-PLAN.md`,
    `PRECOMPILED-PACKS.md`, `d3d-hook-map.md`. Its `CMakeLists.txt` builds portable checks that need
    no SDK, no game, and no GPU.
  - `docs/native-gpu-known-bugs.md`: open issues. Perf-relevant: TEST-20 world/vehicle stalls, slower
    first Toy Pad placement, first-use shader/pipeline compilation hitches.
  - `README-dev.md`: the build guide and hard-won gotchas. Read the "Things that have cost real time" section.
- **SDK:** `DimensionsRecomp/rexglue-sdk`, branch `perf/opt` at the v0.2.0 pin `2897c31`
  (fork branch `codex/dimensions-0.2.0-sdk`). It holds the recompiler (`src/codegen`), the guest-facing
  headers used by every generated translation unit (`include/rex/...`), the kernel HLE (`src/kernel`),
  the system, filesystem and audio code, and the PPC instruction tests (`tests/ppc/asm` plus a bundled
  `tools/binutils`).

## The hard constraint

**We do not have the game files.** The ~470 MB of generated C++ (`rexlego/generated/`) comes from the
user's own Xbox 360 dump plus TU23, so we cannot build or run `legodimensions.exe` or profile real gameplay.
That means:

1. Every change must preserve behaviour and be verifiable without the game: by reasoning, by a
   standalone unit test, by an SDK test (unit or PPC asm), or by a microbenchmark. Make surgical,
   reviewable diffs. **No speculative rewrites and no changes to rendering output.**
2. Prefer *measured* wins. Write a microbenchmark that reproduces the hot pattern and report before
   and after numbers (median of several runs, same machine).
3. Anything that needs the game to validate (risky or large changes, profiling-driven ideas) goes in
   your report as a ranked recommendation, not into the code. The exception is a change that is
   **off by default** behind a cvar or CMake option, where the off path stays byte-for-byte the old behaviour.
4. The shipped baseline is `-march=x86-64-v2` (SSE4.2, SSSE3 OK; **no AVX/AVX2** unless behind runtime
   CPUID dispatch, e.g. `__attribute__((target("avx2")))` plus a cached cpuid check).
5. Keep the code style of the file you are editing. Keep comments short and factual.

## Machine and toolchain

- Windows 11, i7-1255U (2 P-cores and 8 E-cores, 12 threads, AVX2), 32 GB RAM, GeForce MX570 plus Iris Xe.
  **The CPU is shared by 12 agents:** never start more than one heavy build at a time, and cap
  `ninja -j` at 4 unless you are Agent 2 doing the baseline SDK build.
- VS 2022 Community 17.10 (MSVC 14.40) is installed. Its CMake 3.28 and Ninja are under
  `C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\`.
  Clang is **not** installed yet.
- **Agent 2** is setting up `games/lego-dimensions-recomp/env/devshell.ps1` (VS x64 environment, a
  portable LLVM clang, cmake and ninja on PATH) and a baseline SDK build with `compile_commands.json`, plus
  `env/compile-one.ps1` to compile-check a single SDK source file into your own output folder. Until it
  announces them, do analysis and reading. **Agent 3** is building a compile-check harness for `rexlego/src`
  that needs no generated code.
- Standalone tests and benchmarks: put them in `games/lego-dimensions-recomp/bench/agentN/` (your own
  folder). Do not add files to `tools/gpu-aot/` or SDK `tests/` unless your task grants them. The
  orchestrator integrates worthwhile tests at the end.
- Build output goes only under `games/lego-dimensions-recomp/build/agentN/`.

## Rules

- **Only edit files your task grants** (the `files=` list). If you need a change in someone else's
  files, message that agent (or Agent 1) with the exact edit you need.
- **No git commands that change a repository** (commit, checkout, switch, stash, reset, clean, rebase,
  submodule update). Read-only git (log, diff, show, blame, grep) is fine. Agent 1 commits.
- Do not download or touch game data, and do not commit anything derived from the game.
- No network installs except Agent 2 setting up the toolchain.

## Deliverable for every task

1. The code changes in your granted files.
2. A report at `games/lego-dimensions-recomp/perf-notes/agentN-<topic>.md` with:
   - each change: file:line, what, why, risk, and how it was verified (test or bench command and numbers);
   - things you looked at and rejected, with the reason;
   - ranked follow-ups that need the game, a profiler, or a GPU to validate.
3. Finish with `@@done <task>: <3-6 line summary, including the headline numbers>`.
