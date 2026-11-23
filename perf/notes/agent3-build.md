# Agent 3: build system (compile-check harness and flag audit)

**Status: PARTIAL. This session was analysis only.**
- The toolchain was not ready: `env/` was empty, `build/sdk/install` did not exist, and the SDK and plume submodules were empty at 12:25.
- Agent 1 then stopped all builds.
- I did not compile anything and did not edit any source file. Both repos are still clean.
- Every number below is either an estimate or "to measure". The harness design in section 1 is meant to be implemented first thing next session.

`$G` = `games/lego-dimensions-recomp/DimensionsRecomp`, `$S` = `$G/rexglue-sdk`.

---

## 1. Design: stubbing `rexlego/generated/` and `harness/check-rexlego.ps1` (do first next session)

### 1.1 Facts that drive the design
- `$G/rexlego/CMakeLists.txt:17` runs `include(generated/rexglue.cmake)`. `generated/` is gitignored at `rexlego/.gitignore:8`, so the stub cannot dirty the repo.
- The real `generated/rexglue.cmake` is the SDK template `$S/resources/templates/init/rexglue_cmake.inja`, rendered with `snake_case=legodimensions`. It contains:
  - `REXGLUE_RECOMP_DEBUG_INFO`, a CACHE STRING, default `line-tables-only` (inja:35);
  - `REXGLUE_RECOMP_OPTIONS` (inja:40-53): `-fasync-exceptions` on Windows clang (or `/EHa` on MSVC), plus `-gline-tables-only`;
  - those options applied as source COMPILE_OPTIONS (inja:64) and as target options (inja:72);
  - `find_package(rexglue <ver> CONFIG)` when `REXSDK_DIR` is empty;
  - the macro `rexglue_setup_target`. It creates `legodimensions_recomp` (OBJECT) only if `generated/default/sources.cmake` exists, adds the include dirs `.`, `src` and `generated/default`, links `rex::runtime` and calls `rexglue_configure_target`;
  - the custom command `legodimensions_codegen`, which runs `rexglue codegen` on the XEX. The stub must make this an empty `add_custom_target`.
- `rexglue_configure_target` (`$S/cmake/rexglue_helpers.cmake:77-111`) adds `${REXGLUE_SHARE_DIR}/windowed_app_main_sdl.cpp` and `rex_app.cpp`, defines `REXGLUE_BUILD_CONFIG`, adds `-msse4.1` (helpers:60) and Windows POST_BUILD DLL copies.
- These generated headers are included by `rexlego/src` (74 TUs):

  | Header | Included by |
  |---|---|
  | `default/legodimensions_init.h` | `main.cpp` |
  | `default/legodimensions_pch.h` | `crash_guards.cpp`, `native_atomics.cpp`, `native_constants.cpp`, `native_lock_elide.cpp`, `native_memops.cpp`, `native_saverest.cpp` |
  | `default/legodimensions_funcs.{154,254,302,389,393,395,410}.h` | `native_lock_elide.cpp` only |

  All other TUs declare their guest externs themselves through `rex/hook.h` (`REX_EXTERN`, `REX_HOOK*`, `REX_FUNC`).
- `LEGODIMENSIONS_NATIVE_GPU` defaults to OFF (`CMakeLists.txt:22`), but the shipped 0.2.0 is the "Native GPU" build (`README.md:18`). Both configs have to compile:
  - With OFF, everything except `src/gpu_native/**` compiles.
  - With ON, configure needs the private shader banks, the plume submodule, FidelityFX headers and DXC (section 1.4).
- With Ninja, every `legodimensions` object order-depends on all custom commands and `add_dependencies`: DXC headers, prelink tools, linked caches and the fingerprint. "Compile one TU" through the normal graph would build the GPU pipeline first.
- **Decision:** the harness compiles from `compile_commands.json` (`CMAKE_EXPORT_COMPILE_COMMANDS=ON`), outside CMake's Ninja graph.

### 1.2 Files (all owned by Agent 3)
```
harness/stub-generated/                 # source of truth; copied into rexlego/generated/
  .rexlego-compile-check-stub           # marker; the harness refuses to touch a generated/ without it
  rexglue.cmake                         # rendered inja with codegen = add_custom_target(legodimensions_codegen)
  default/legodimensions_pch.h          # pch_h.inja rendered with plausible constants (below)
  default/legodimensions_init.h         # #pragma once + pch + funcs (mirrors init_h.inja)
  default/legodimensions_funcs.h        # DECLARE_REX_FUNC(...) for every guest symbol the src TUs need
  default/legodimensions_funcs.N.h      # N in 154,254,302,389,393,395,410: #pragma once + #include "legodimensions_funcs.h"
  default/sources.cmake                 # OPTIONAL: one tiny recomp TU so legodimensions_recomp's flag path
                                        # (-O3, -march, PCH, -fasync-exceptions) is exercised for Part B
harness/gen-stub-generated.ps1          # regenerates funcs.h by scanning src (regex below)
harness/check-rexlego.ps1               # the entry point
harness/stubs/native-gpu/               # banks / caches for NATIVE_GPU=ON (section 1.4)
```
- **`rexglue.cmake`:**
  - Copy the inja and resolve its `{{ }}` and `{% %}` by hand. With `REXSDK_DIR` empty, keep `find_package(rexglue CONFIG REQUIRED)`; the harness passes `-DCMAKE_PREFIX_PATH=<repo>/build/sdk/install`.
  - Drop the version floor, or keep 0.10. The SDK floor is 0.10.0.
  - Check first whether `rexglue init` in the SDK install can render this file without a XEX. If it can, use its output and only patch out codegen.
- **`legodimensions_pch.h`:**
  - Copy `$S/resources/templates/codegen/pch_h.inja` and substitute: `REX_IMAGE_BASE 0x82000000`, `REX_CODE_BASE`/`REX_CODE_SIZE` covering `0x82A20188..0x83FD1470` (the range of the `sub_` names in src), `REX_IMAGE_SIZE`, `REX_THUNK_RESERVE_SIZE`, `REXCRT_HEAP`. Imports sit around 0x8411xxxx.
  - Resolve the `REX_CONFIG_*` `{% if %}` blocks from `rexlego/legodimensions_config.toml` (I have not read it yet).
  - Keep every macro body verbatim, so object code matches the real build: `REX_LOAD_*`/`REX_STORE_*` (pch_h.inja:136-145), `REX_FUNC_PROLOGUE`, `REX_CALL_INDIRECT_FUNC`, `ppc_setjmp`/`ppc_longjmp`, `ppc_global_lock_count_`, `REX_*_GLOBAL_LOCK`, and so on.
- **`legodimensions_funcs.h`:**
  - Collect every match of `\b(sub_[0-9A-F]{8}|__(save|rest)(gpr|fpr|vmx)(lr)?_\d+)\b` in `native_lock_elide.cpp` (and in any other TU that includes the pch).
  - Subtract the names the TU declares itself: `__imp__sub_82A2CAB0`, `82A2CC20`, `82A34E28`, `82A34FE8`, `82A4CA18`, `82A35D28`, `83F99CB8`.
  - Emit `DECLARE_REX_FUNC(name);` for each name that remains.
- No definitions are needed, because link failures are acceptable.

### 1.3 `harness/check-rexlego.ps1 [-Files <paths>] [-OutDir <dir>] [-Jobs <1-4>] [-NativeGpu] [-Reconfigure]`
1. Dot-source `env/devshell.ps1` from Agent 2.
2. Install the stub into `rexlego/generated/`:
   - if `generated/` is missing, or carries the marker, sync it;
   - if a real `generated/` exists (no marker), use it as is; this is a real compile check.
3. Configure once. Re-run only on `-Reconfigure` or when `CMakeLists.txt`, `CMakeCache` or the stub is newer. Build tree: `build/agent3/rexlego-cfg[-gpu]`, no spaces in the path (README warns that spaces break depfiles).
   ```
   cmake -S $G/rexlego -B build/agent3/rexlego-cfg -G Ninja -DCMAKE_BUILD_TYPE=Release
     -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_PREFIX_PATH=<repo>/build/sdk/install
     -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DLEGODIMENSIONS_X86_BASELINE=x86-64-v2   # shipped value, see 2.1
     [-DLEGODIMENSIONS_NATIVE_GPU=ON + the stub cache vars of 1.4]
   ```
4. Read `compile_commands.json` and keep the entries whose `file` is under `rexlego/src` (or matches `-Files`). Also keep the `cmake_pch.hxx.cxx` entries, because the game/recomp target uses a PCH (`SKIP_PRECOMPILE_HEADERS` is set on several sources at `CMakeLists.txt:273,282,495,501`).
5. Write `OutDir/check.ninja`:
   - one `rule cc` with `command = $cmd -MD -MF $out.d`, `deps = gcc` and `-o` rewritten into `OutDir` (default `build/agent3/check`);
   - PCH edges first, with every TU order-depending on its `.pch`.
   - Then run `ninja -f check.ninja -j<Jobs≤4> -k 0`. This gives free incremental rebuilds and a hard cap of -j4.
6. For `-NativeGpu`, generate the build-time headers before running ninja:
   - DXC shader headers into `<bin>/generated/gpu_native/shaders/*.h` (`g_<name>_dxil`) and `native_overlay_{vs,ps}.h`, using the Windows SDK `dxc.exe` (`C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\dxc.exe`);
   - `native_gpu_build_info.h` from `src/gpu_native/build_info.h.in` with a fixed `compile-check` fingerprint.
7. Print PASS/FAIL per file plus the first diagnostics, and a total time. Exit 1 if anything failed.

Usage to post once it works:
```
pwsh -File harness/check-rexlego.ps1                                  # all rexlego/src TUs, Release flags, -j4
pwsh -File harness/check-rexlego.ps1 -Files src/native_lock_elide.cpp,src/main.cpp -OutDir build/agentN/check
pwsh -File harness/check-rexlego.ps1 -NativeGpu                       # include src/gpu_native/** (needs 1.4)
```

### 1.4 NATIVE_GPU=ON configure requirements, and the stub for each
| Requirement (`rexlego/CMakeLists.txt`) | Stub |
|---|---|
| `LEGO_TEMPORAL_SHADER_BANK/temporal-bank.{obj,cpp}` (182-191). The .cpp is `#include`d through `LEGO_TEMPORAL_SHADER_METADATA` | empty COFF obj (`clang -c -x c NUL -o temporal-bank.obj`) plus a .cpp with the declarations the including TU expects (read `temporal_shaders.cpp` first) |
| `LEGO_FLOAT_BLEND_INDICES_BANK/float-blend-indices-bank.{obj,cpp}` (192-200) | same approach |
| `LEGO_NATIVE_SHADER_CACHE` (about 262-273) and `LEGO_NATIVE_RUNTIME_SHADER_CACHE` (283+) | minimal .cpp defining the symbols the cache readers use |
| `LEGO_NATIVE_MICROCODE_INDEX`, **hard-coded** to `rexlego/out/native-gpu/lego-microcode-index.cpp` (274-275) | needs a 1-line change to `CACHE FILEPATH` with the same default (no behaviour change; diff in 3.9), or a file in `rexlego/out`, which I do not own |
| `LEGO_NATIVE_FIDELITYFX_RUNTIME` (find_file) | any existing file path |
| `prepare_plume.py --check` and Python3 | needs the **plume submodule populated and patched** (Agent 2 or Agent 1) |
| FidelityFX-SDK headers (`fsr3_upscaler.cpp`) | needs the **SDK `thirdparty/FidelityFX-SDK` submodule** |
| `LEGO_HOST_DXC_EXECUTABLE`, `LEGO_DXC_ROOT` (prelink tools only) | Windows SDK dxc. `LEGO_DXC_ROOT` only matters for `lego_gpu_prelink*` (388-408), which the harness never builds |
| `LEGO_NATIVE_BINARY_CACHE` (defaults ON when clang, llvm-mc and Python are found) | pass OFF explicitly. With OFF, `runtime_linked_shader_cache.cpp` includes `../../out/native-gpu/runtime-linked-dxil-cache.cpp`, which still needs a stub, so read that TU first |

If plume or FidelityFX cannot be populated, ship the OFF config first. It covers every non-GPU TU and unblocks Agents 4-8. `src/gpu_native/**` is then reported as "needs submodules".

---

## 2. Flag audit: what the build does today (from reading only)

### 2.1 Per target
| Target | Opt | `-march` | FP model | Aliasing | Debug info | Source |
|---|---|---|---|---|---|---|
| SDK (all targets, including thirdparty) | Release `-O3 -DNDEBUG`, RelWithDebInfo uses the CMake default `-O2 -g` | presets put `-march=x86-64-v2` in `CMAKE_C/CXX_FLAGS` (`$S/CMakePresets.json:17-18,40-41`; mac-amd64 v3 at 63-64), so the `REXGLUE_X86_BASELINE` logic (`$S/CMakeLists.txt:71-83`) stands back | `-ffp-model=strict` (`$S/CMakeLists.txt:166`) | `-fno-strict-aliasing` (165) | Release: none | `$S/CMakeLists.txt:164-172` |
| `legodimensions` (hand-written game) | `CMAKE_CXX_FLAGS_RELEASE`, the CMake default `-O3 -DNDEBUG` | `LEGODIMENSIONS_X86_BASELINE`, **default `x86-64-v3`** (`CMakeLists.txt:840,847`) | **clang default** (`precise`, so `-ffp-contract=on`) | clang default: relaxed on `*-windows-msvc`, **strict on Linux** | Release: none | `CMakeLists.txt:843-848` |
| `legodimensions_recomp` (generated) | `-O3` for Release and RelWithDebInfo (851) | same baseline (853-854) | **clang default** (`-ffp-contract=on`) | same as above | `-gline-tables-only` (inja:53) | `CMakeLists.txt:849-856`, `rexglue_cmake.inja:40-72` |

The SDK's `add_compile_options(-ffp-model=strict -fno-strict-aliasing)` is directory-scoped. A grep of `$S/**/CMakeLists.txt` and `cmake/*` finds no exported `INTERFACE_COMPILE_OPTIONS`, so **neither flag reaches the game project**. The harness's `compile_commands.json` will confirm this.

**Baseline discrepancy (needs a decision from the maintainer or Agent 1):**
- `README.md:431-436`: everything has been built for **x86-64-v2** since 0.1.30.
- `rexlego/CMakeLists.txt:840` still defaults the game and the recomp code to **v3**, and `README-dev.md:110` still says "shipped builds target x86-64-v3".
- So either the release script passes `-DLEGODIMENSIONS_X86_BASELINE=x86-64-v2`, or the shipped exe is really v3 and needs AVX2. I have not read `RELEASING.md` or the installer script.
- A default configure today gives a v3 game linked to a v2 SDK. That is fine on AVX2 CPUs, but it is not what ships.
- Proposed (safe, matches shipped behaviour): change the default at line 840 to `x86-64-v2`, and fix the comment at 823-826 and `README-dev.md:110`. The harness passes v2 explicitly either way.

### 2.2 Other facts
- **Guest FMA is explicit.** `$S/src/codegen/builders/floating_point.cpp:200-242` emits `std::fma(...)` for fmadd, fmsub, fnmadd and fnmsub, single and double.
  - On **v2** this lowers to a **call to the CRT `fma`**: a libcall per guest FMA, volatile XMM clobbers, and a software path on CPUs without FMA3.
  - On **v3** it is one `vfmadd`.
  - Both are correctly rounded, so **the results are bit-identical**.
- **`vmaddfp` is unfused:** `simde_mm_add_ps(simde_mm_mul_ps(...))` (`vector.cpp:93-99`). The mul and add sit in different inline functions, so `-ffp-contract=on` does not fuse them. It is the same on v2 and v3.
- **Contraction risk on v3:** any `a*b+c` written as one expression in hand-written game code (`native_*.cpp`, gpu_native) or in a generated statement **is fused on v3 and not on v2** under clang's default `-ffp-contract=on`. That is the only FP-result difference between the two baselines I could find. Fix: 3.2.
- **Guest memory access is `volatile`** (`pch_h.inja:136-145`: `__builtin_bswap32(*(volatile u32*)(base+...))`). This blocks load/store forwarding, dead-store elimination, hoisting and vectorisation of guest memory ops in all recompiled code. It is a codegen-semantics issue (MMIO and cross-thread visibility), not a flag. It is noted for the codegen owner, possibly a large win, high risk.
- **`/OPT:REF` and `/OPT:ICF`:** not set anywhere. lld-link and link.exe default to REF+ICF *unless* `/DEBUG`. Release compile flags carry no `-g`, so the Release link most likely has no `/DEBUG`. Then REF and ICF are already on, and the recomp `-gline-tables-only` is **thrown away at link time** (see 3.3). To verify: inspect the link line.
- **Function sections:** not set. COFF ICF only folds COMDAT sections, so today only inline and template functions can fold. Recomp functions are all referenced from `PPCFuncMappings`, so REF cannot drop them.
- **Frame pointers:** not set. On Windows x64 this does not matter, because unwinding uses `.pdata`. The SDK uses `-fno-omit-frame-pointer` only with sanitizers (`$S/CMakeLists.txt:266`).
- **Linux:** `-mcmodel=large` is set globally (`$S/CMakeLists.txt:155`) and per host target (helpers:52, plus `-Wl,--no-relax` at 51). Its comment cites "35MB+" executables, which fit easily in the small or medium model. The large model turns every call and global access into `movabs` + indirect. This is a possible sizeable Linux-only win; follow-up 4.3.
- **Debug and diagnostic defines in Release:** none leak.
  - Perf counters are defined only for non-Release (`$S/CMakeLists.txt:31`). Tracy is gated the same way (27-29; my earlier read).
  - `LEGODIMENSIONS_TT_LOCK_TRACE` (144) and `LEGODIMENSIONS_DEV_PROBES` (161, global `add_compile_definitions` at 165) are OFF.
  - `REXGLUE_BUILD_CONFIG` is defined twice, at `$S/CMakeLists.txt:216` and helpers:85. Same value, harmless.
  - `-msse4.1` (helpers:60) is redundant under `-march=x86-64-v2` and harmless.
- **PCH:** the SDK uses `rex_target_pch` (`$S/cmake/rex_pch.cmake:1-5`). Recomp code uses the generated pch (template). The game target has a PCH (shown by the `SKIP_PRECOMPILE_HEADERS` lines); confirm from `compile_commands.json`. **Unity builds:** none.
- **ThinLTO:** `LEGODIMENSIONS_THIN_LTO` exists and is OFF (`CMakeLists.txt:862-885`). It covers `legodimensions`, `legodimensions_recomp` and `plume`, with `/opt:lldltojobs=2` and `/lldltocache`. Nothing selects lld, though: no `-fuse-ld=lld` and no `CMAKE_LINKER_TYPE` in the presets. clang's MSVC driver uses `link.exe` by default, which cannot take bitcode. To verify: which linker the link line runs.

---

## 3. Ranked proposals (none applied; each needs the harness or the game)

### 3.1 Optional x86-64-v3 game exe plus a CPUID launcher (OFF by default). Largest expected CPU win
- **Evidence:** v2 turns every guest `fmadd*` into a libcall (2.2).
  - PPC code is dense in `rlwinm`/`slw`/`srw`/`rlwimi`. BMI2 `shlx`/`shrx`/`rorx` remove the CL shuffling and copies.
  - VMX per-element shifts (`vslw`/`vsrw`/`vsraw`) need AVX2 `vpsllvd`/`vpsrlvd`/`vpsravd`; otherwise simde emulates them.
  - VEX 3-operand encoding removes `movaps` copies.
  - `CMakeLists.txt:825` cites TheSimpsonsGameRecomp measuring v3 + `-O3` as "a real win". This game was moved to v2 for compatibility (`README.md:431-436`), so the win is currently left on the table for AVX2 users.
- **Change, minimal-risk version** (no refactor of the 885-line file):
  1. `CMakeLists.txt`: add `set(LEGODIMENSIONS_OUTPUT_SUFFIX "" CACHE STRING ...)` and `set_target_properties(legodimensions PROPERTIES OUTPUT_NAME "legodimensions${LEGODIMENSIONS_OUTPUT_SUFFIX}")`. Make the `/MAP` at line 178 follow the output name.
  2. `CMakePresets.json`: add `win-amd64-release-v3` with `LEGODIMENSIONS_X86_BASELINE=x86-64-v3` and `LEGODIMENSIONS_OUTPUT_SUFFIX=-v3`, in its own binary dir. It uses the same v2 SDK install, which is safe: v2 ⊂ v3, the v3 exe only runs where AVX2 exists, and nothing crosses the DLL ABI as `__m256`.
  3. `option(LEGODIMENSIONS_LAUNCHER OFF)` → `add_executable(legodimensions_launcher WIN32 launcher/launcher.cpp)`. The launcher, about 100 lines with kernel32 only:
     - checks CPUID.1:ECX FMA(12), MOVBE(22), OSXSAVE(27), AVX(28), F16C(29);
     - checks CPUID.7.0:EBX BMI1(3), AVX2(5), BMI2(8), and CPUID.80000001h:ECX LZCNT(5);
     - checks XGETBV(0) & 6 == 6 (use inline asm, or compile with `-mxsave`);
     - starts `legodimensions-v3.exe` if it is present and supported, else `legodimensions.exe`, with `CreateProcessW`, the original command-line tail (parse a quoted argv0), the inherited cwd and handles;
     - supports the env override `LEGODIMENSIONS_FORCE_V2=1`;
     - waits, then returns the child's exit code, using a kill-on-close job object.
  4. Packaging (not mine): ship both exes, and point shortcuts at the launcher.
  5. Both builds must get 3.2, or v3 can differ from v2 in FP results.
- **Risk:**
  - build time doubles for the release (the recomp TUs are compiled twice);
  - ship size grows by one more exe;
  - shortcut and installer changes;
  - `__AVX2__` paths in hand-written code (`constant_compare.h:16`, `index_bounds.h:5,29`) are integer-only but must be checked.
- **Verify:**
  - compile both;
  - `llvm-objdump -d legodimensions.exe | Select-String 'call.*\bfma\b'` (v2) against a `vfmadd` count (v3) should match the `std::fma` sites;
  - test the launcher by masking CPUID (`LEGODIMENSIONS_FORCE_V2`) and on a non-AVX2 VM;
  - **with the game:** guest-state hash or replay determinism (v2 against v3 must be bit-identical) and CPU-bound frame time.

### 3.2 `-ffp-contract=off` on `legodimensions` and `legodimensions_recomp` (safe; FP-preserving)
- **Evidence:** 2.1 and 2.2. The SDK is FP-strict, but the game project inherits clang's `-ffp-contract=on`. On v2 there is no FMA hardware, so `llvm.fmuladd` lowers to mul+add and this flag **changes no codegen**. On v3 builds (including today's CMake default) it restores v2-identical results.
```cmake
# Guest FP must not depend on the -march baseline: never fuse a*b+c into FMA
# (std::fma in generated code stays exact either way).
target_compile_options(legodimensions PRIVATE -ffp-contract=off)
if(TARGET legodimensions_recomp)
    target_compile_options(legodimensions_recomp PRIVATE -ffp-contract=off)
endif()
```
- **Risk:** none on v2. On v3 builds, `a*b+c` expressions in hand-written code lose fusion, which is the intended effect.
- **Verify:** compile-check all TUs. Compare v2 `.obj` code bytes before and after the flag (`llvm-objcopy --dump-section .text`, or `llvm-objdump -d`), which should be identical. In v3 objects, the `vfmadd` count should equal the explicit fma sites.

### 3.3 Release debug-info and linker consistency (build-time win, zero runtime risk)
- **Evidence:**
  - recomp TUs compile with `-gline-tables-only` (inja:35,53);
  - the Release link likely has no `/DEBUG`, since the `/MAP` at `CMakeLists.txt:178` exists "for offline symbolization", which suggests no PDB;
  - if so, the line tables are discarded at link time and only cost compile time and `.obj` size on the largest part of the build.
- **Change:**
  - If the link line has **no** `/DEBUG`: set `"REXGLUE_RECOMP_DEBUG_INFO": "none"` in the release presets of `rexlego/CMakePresets.json`. It is a cache var of the generated file, so no generated or SDK edit is needed.
  - If it **has** `/DEBUG` (a PDB ships): add `"LINKER:/OPT:REF" "LINKER:/OPT:ICF"` for Release explicitly, because `/DEBUG` turns them off.
- **Risk:** none at runtime. Confirm that crash symbolization (`crash_guards.cpp`) does not need a PDB.
- **Verify:**
  - `ninja -C build/agent3/rexlego-cfg -t commands legodimensions | Select-String 'lld-link|link.exe|/DEBUG|/OPT'`;
  - recomp `.obj` size and compile time before and after (median of 3, at -j1);
  - exe size unchanged.

### 3.4 `LEGODIMENSIONS_PGO=OFF|GEN|USE` (OFF by default; needs the game for a profile)
```cmake
set(LEGODIMENSIONS_PGO "OFF" CACHE STRING "Clang PGO: OFF, GEN (instrument) or USE")
set_property(CACHE LEGODIMENSIONS_PGO PROPERTY STRINGS OFF GEN USE)
set(LEGODIMENSIONS_PGO_PROFILE "${CMAKE_CURRENT_SOURCE_DIR}/pgo/legodimensions.profdata"
    CACHE FILEPATH "llvm-profdata merged profile for LEGODIMENSIONS_PGO=USE")
if(NOT LEGODIMENSIONS_PGO STREQUAL "OFF")
    if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
        message(FATAL_ERROR "LEGODIMENSIONS_PGO requires Clang")
    endif()
    if(LEGODIMENSIONS_PGO STREQUAL "GEN")
        set(LEGO_PGO_FLAGS -fprofile-instr-generate)
        target_link_options(legodimensions PRIVATE -fprofile-instr-generate)  # pulls clang_rt.profile
    elseif(LEGODIMENSIONS_PGO STREQUAL "USE")
        if(NOT EXISTS "${LEGODIMENSIONS_PGO_PROFILE}")
            message(FATAL_ERROR "LEGODIMENSIONS_PGO=USE needs ${LEGODIMENSIONS_PGO_PROFILE}")
        endif()
        set(LEGO_PGO_FLAGS "-fprofile-instr-use=${LEGODIMENSIONS_PGO_PROFILE}"
            -Wno-profile-instr-unprofiled -Wno-profile-instr-out-of-date)
    else()
        message(FATAL_ERROR "LEGODIMENSIONS_PGO must be OFF, GEN or USE")
    endif()
    foreach(LEGO_PGO_TARGET IN ITEMS legodimensions legodimensions_recomp)
        if(TARGET ${LEGO_PGO_TARGET})
            target_compile_options(${LEGO_PGO_TARGET} PRIVATE ${LEGO_PGO_FLAGS})
        endif()
    endforeach()
endif()
```
- **Notes:**
  - IR PGO (`-fprofile-generate`/`-fprofile-use`) usually has lower runtime overhead and optimises better than front-end `-fprofile-instr-*`. Offer it as `LEGODIMENSIONS_PGO_KIND=IR|FE` and measure both.
  - The profile is written from `atexit`. If the game leaves through `ExitProcess`/`TerminateProcess` or a crash guard, nothing is written; the quit path then needs `__llvm_profile_write_file()` (game src, not mine).
  - Use `LLVM_PROFILE_FILE=legodimensions-%p-%m.profraw`.
  - The profile goes stale when codegen changes the generated TUs.
- **Risk:** OFF by default, so none to the shipped build. USE changes code layout and inlining but not semantics.
- **Verify:**
  - GEN builds and runs, and `.profraw` appears;
  - `llvm-profdata merge`;
  - USE builds without mismatch warnings flooding the log;
  - CPU frame time on a fixed scene (game).

### 3.5 ThinLTO: make the existing option actually usable (OFF by default)
- **Evidence:** `CMakeLists.txt:862-885` never selects lld (2.2).
- **Change:** inside `if(LEGODIMENSIONS_THIN_LTO)` on WIN32, add `target_link_options(legodimensions PRIVATE -fuse-ld=lld)` (or `CMAKE_LINKER_TYPE=LLD` with CMake ≥ 3.29). Keep the existing name. Do not add a second `LEGODIMENSIONS_THINLTO` spelling; one knob is enough.
- **Expected win:** cross-TU inlining of small guest functions and the `__savegprlr_N`/`__restgprlr_N` helpers into callers.
- **Risk:** link memory and time; the existing 2-job limit has a 16 GB note.
- **Verify:** configure passes `check_ipo_supported`, the link runs lld-link (visible in the link line), and link time, peak RSS and `.text` size are recorded; then frame time (game).

### 3.6 Function sections + ICF experiment (OFF by default; `LEGODIMENSIONS_ICF`)
- **Change:** `-ffunction-sections` on recomp code plus `LINKER:/OPT:ICF`, to fold byte-identical guest functions. The expected effect is a few % of `.text` and better i-cache use.
- **Risk:** folded functions share one host address. Guest calls stay correct, but `/MAP` symbolization (sample_profiler) and any host-pointer identity check (hook tables in `rex/hook.h`) break. Audit before trying.
- **Verify:** `.text` size and map diff.

### 3.7 Build time
- **Keep:**
  - PCH as is. Confirm the game target's PCH in `compile_commands.json`. If it is missing, add `target_precompile_headers(legodimensions PRIVATE <rex/...> <imgui.h> ...)`, guided by `-ftime-trace` on the 5 slowest TUs.
- **Measure first:**
  - per-TU compile time of all 74 TUs through the harness at -j1, to find the outliers;
  - `-ftime-trace` on the slowest.
- **Unity builds:** rejected for recomp (section 5). For the 74 hand-written TUs, maybe later; it risks static-name collisions.

### 3.8 SDK RelWithDebInfo uses `-O2`, Release uses `-O3` (low priority)
`$S/CMakeLists.txt:168-170` only overrides Release, so profiling builds of the SDK do not represent Release. Adding `$<$<CONFIG:RELWITHDEBINFO>:-O3>` makes them equal. The risk is a slightly slower debug experience. Verify with the effective flags of a RelWithDebInfo SDK object (`-###`).

### 3.9 Harness enabler (behaviour-preserving)
Make `LEGO_NATIVE_MICROCODE_INDEX` (`CMakeLists.txt:274-275`) a cache path with the same default, so the harness can point it at a stub:
```cmake
set(LEGO_NATIVE_MICROCODE_INDEX
    "${CMAKE_CURRENT_SOURCE_DIR}/out/native-gpu/lego-microcode-index.cpp"
    CACHE FILEPATH "Microcode index generated by lego_gpu_microcode_index")
```

---

## 4. Follow-ups that need the game, a profiler or a GPU (ranked)
1. **v2 against v3 guest-state determinism and frame time** (3.1 + 3.2). Needs the game and a fixed scene or replay; hash FPR/VR/memory at frame boundaries.
2. **PGO profile collection** (3.4). Needs a representative play session; check whether atexit runs.
3. **Linux `-mcmodel=large` → `small`/`medium`** (`$S/CMakeLists.txt:151-158`, helpers:50-52). Needs a Linux build and the game. Possibly a sizeable win on Linux; SDK design decision.
4. **`volatile` guest loads and stores** (`pch_h.inja:136-145`). Codegen owner; needs the game (threads, MMIO).
5. **`-fasync-exceptions` cost on recomp code** (inja:45). Compare object code with and without it. It is needed for SEH and `ppc_longjmp` unwinding, so only an experiment.
6. **FP environment:** the generated code toggles MXCSR (`emit_set_flush_mode`, vector.cpp:94) while compiled without `-ffp-model=strict`, so LLVM may legally move FP ops across `ldmxcsr`. Making it strict would cost a lot of performance and change codegen. Needs a game-side FTZ/DAZ correctness check first; do not change blindly.
7. ThinLTO (3.5) and ICF (3.6) frame-time and size measurements.

## 5. Rejected
- `-ffast-math`, `-ffp-contract=fast`, `-fassociative-math`, dropping `-ffp-model=strict` in the SDK: these change guest or host FP results.
- Dropping `-fno-strict-aliasing` in the SDK: the codebase type-puns, and the risk outweighs any gain.
- `-march=native` or a global v3 SDK: not shippable; breaks v2 users (`README.md:431-436`).
- Full LTO: memory and link time with the recomp objects. ThinLTO only.
- Unity builds for recomp TUs: they are already large generated chunks; this would hurt memory and parallelism.
- `target_clones` multiversioning of guest functions: doubles code size, adds per-call dispatch, and needs ifunc-like support on COFF. The launcher (3.1) is simpler.
- Frame pointers by default: no use on Win64 (`.pdata` unwinding). At most a Linux profiling-only option.

## 6. Not read or not done
- **Not done:**
  - no build, no measurement, no stub files.
  - `harness/check-rexlego.ps1` exists only as a **draft** that implements 1.3. It passes the PowerShell parser and has **never been run**. `harness/stub-generated/` and `harness/stubs/native-gpu/` do not exist yet.
  - `@@to 4-8: rexlego compile-check ready` was **not** posted; Part A is not ready.
- **Not read:**
  - `RELEASING.md` and the installer or release scripts. These settle the shipped `-march` (2.1) and whether a PDB or `/DEBUG` ships (3.3).
  - `rexlego/legodimensions_config.toml`, for the pch `REX_CONFIG_*` values.
  - the full `native_lock_elide.cpp` guest-symbol list, and `native_constants.cpp`, `native_memops.cpp`;
  - `src/gpu_native/{temporal_shaders,float_blend_indices,instanced_constants,runtime_shader_cache,runtime_linked_shader_cache,shader_archive,pipeline_library}.cpp`, for what the stub banks and caches must declare. Also where `ghostbusters_water_ps.h` and `gpu_native/integer_input_bank.inc` come from;
  - `tools/gpu-aot/prepare_plume.py`, `src/gpu_native/build_info.h.in`;
  - SDK `include/rex/ppc.h`, `hook.h`, `rex_app.h`, `src/*/CMakeLists.txt` (multi-line `PUBLIC` compile options), `cmake/rexglue_fidelityfx.cmake`;
  - CMake's Windows-Clang default link flags, to confirm `/DEBUG` behaviour per config.
- **Blockers for next session:**
  - Agent 2: the SDK install at `build/sdk/install` and `env/devshell.ps1`;
  - populated `thirdparty/plume` (plus `prepare_plume.py`) and `rexglue-sdk/thirdparty/FidelityFX-SDK`, needed only for `-NativeGpu`.
