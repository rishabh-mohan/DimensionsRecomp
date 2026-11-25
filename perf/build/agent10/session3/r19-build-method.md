# #19 build method ruling: dependency-scoped recompile of rexgpu-xenos (devoff4b-r19-bin)

M10 (safety reviews), 2026-11-25 02:43. Read-only review. I compiled and ran nothing. My only scripts were two read-only scanners, which read `.ninja_deps` and PE headers.

## Files rated (sha256 first 16, size; hashed at 02:42)

| file | sha256 | bytes |
|---|---|---|
| `agent7/s4-r1s2/s4-r1s2.diff` | 06B0D371686CD384 | 20060 |
| `agent2/s33/r19/prep.txt` | ADA5D09E516239DF | 5308 |
| `agent2/s33/r19/list-on.tsv` | 99BD9ED6BDFEC1A5 | 3539 |
| `agent2/s33/r19/replace-on.txt` | 3ED7ADD07ECC1AF6 | 1792 |
| `agent2/session3/prep-s33.py` | A311E35401ABE799 | 7881 |
| `agent2/session3/build-bin.py` | 2B033FC60DAC29D2 | 10434 |
| `agent2/recompile.py` | 88A94B5CC54B9CDA | 8934 |
| `agent2/relink.py` | F3C6EEAF332AB213 | 17091 |
| `agent2/snap1-sdk/.ninja_deps` | E1977460AB41AAA4 | 2370708 |
| `agent2/devoff4b-bin/rexgpu-xenos.dll` | E3CB99CFDEA95E66 | 3425792 |
| `agent10/session3/scratch-r19build/ninja_deps_scan.py` | 4F3CBDB22A9A2ED0 | 2285 |
| `agent10/session3/scratch-r19build/pe_scan.py` | 9801325619C7A7AD | 2464 |

`build-bin.py` and `recompile.py` changed size between 02:40 (10108 / 8491 B) and 02:42. M2 is still editing them. The conditions below apply to whatever version actually runs.

## Base

- snap1-sdk Release (759 obj/pch edges, `.ninja_deps` v4, 759 outputs with deps).
- devoff4b-bin `rexgpu-xenos.dll` E3CB99CF, which is the shared install DLL.
- This ruling replaces r19-rating.md (a) item 2, "full SDK rebuild, not a relink", for this bin only.

## Verdict: ACCEPT-IF

The full rebuild in (a) was the conservative default, chosen because `command_processor.h` changes a class layout. I checked the evidence, and the layout change cannot reach anything outside the 9 TUs M2 lists:

1. **Header consumers (snap1-sdk).** I parsed `.ninja_deps` myself:
   - `d3d12/command_processor.h` is included by 8 objects, all of them `rexgpu-xenos.dir/Release/d3d12/*`.
   - `d3d12/deferred_command_list.h` is included by those 8 plus `plugin_main.cpp.obj`.
   - That makes 9 objects, matching M2's list exactly. No other SDK target includes either header: not rexruntime, not TracyClient, not the vulkan backend, not any other DLL.
2. **Header consumers (game builds).** In snap1-off and snap1-on `.ninja_deps`, 0 objects include either header, and 0 paths end in `command_processor.h` or `deferred_command_list.h` at all (not even the base `rex/graphics/command_processor.h`). The exe has no view of the class.
3. **DLL boundary.**
   - `rexgpu-xenos.dll` exports only 4 names: `rex_gpu_create`, `rex_gpu_abi_version`, `NvOptimusEnablement` and `AmdPowerXpressRequestHighPerformance`.
   - In devoff4b-bin, neither `legodimensions.exe`, `rexruntime.dll` nor `TracyClient.dll` statically imports anything from it; it is loaded as a plugin.
   - The patch touches no base or ABI header (5 files, all `d3d12/`), so the plugin ABI and the base-class vtables are unchanged.
4. **PCH.** rexgpu-xenos is compiled with `-include-pch .../rexgpu-xenos.dir/Release/cmake_pch.hxx.pch`. That PCH does not depend on either changed header (it is not among the matching outputs), so reusing it is safe.
5. **Inline functions, ODR, vtables.**
   - Every TU that sees the class definition gets recompiled, so all COMDAT copies of its inline functions come from the new header.
   - Its vtable comes from `command_processor.cpp`, which is recompiled too.
   - The other 28 rexgpu-xenos objects never see the definition.
   - I found no static LTO and no `/GL`. The flags are `-O3 -march=x86-64-v2`, with no `-flto`.
6. **Include resolution.**
   - Every include of the two headers in the SDK uses angle brackets with the full path (`<rex/graphics/d3d12/...>`). There are no relative quoted includes.
   - The overlay `sdk/include` holds only the two patched headers.
   - With `--include-first <overlay>/include` placed right after the compiler, both headers resolve to the overlay copy in all 9 TUs; everything else still resolves to snap1.
   - Both headers use `#pragma once`.
7. **Control.** `build-bin.py` runs a CTL leg: it recompiles the 9 unpatched TUs and relinks, and the result must equal the devoff4b-bin DLL except for timestamps.
   - `relink.py` `pe_compare` allows only 4-byte runs that match the TimeDateStamp. A DIFF returns rc 4, and build-bin fails the CTL step on rc != 0.
   - This proves the ccdb command lines, PCH and link inputs rebuild the shipped DLL exactly.

## Conditions

- **C1 (BLOCKER if not met): the CTL leg must really PASS.** The only CTL run so far was the 02:38 dry run, so its "FAIL CTL relink" is the expected missing-object failure.
  - Required: a real `PASS compare ... identical except N TimeDateStamp field(s)` (or `byte-identical`) against devoff4b-bin `rexgpu-xenos.dll` E3CB99CF.
  - If it shows DIFF or fails, stop. Either the full SDK rebuild from r19-rating (a) applies, or bring it back to me.
- **C2 (BLOCKER if not met): overlay include on every ON TU.**
  - `log-on/recompile-commands.txt` must show `-I<WS>/build/agent2/s33/r19/sdk/include` ahead of the snap1 `rexglue-sdk/include` on all 9 command lines.
  - Each ON compile must use the overlay `.cpp` where one exists, and snap1's copy otherwise, as in list-on.tsv.
  - SHOULD: add `-MD -MF <log-on>/<tu>.d` to the ON compiles (it does not change object code). Then confirm that each depfile names the overlay copies of both headers and never the snap1 copies.
- **C3: reuse the existing PCH unchanged.** Any PCH validation error or warning (for example "file has been modified since the precompiled header was built") means stop. Do not rebuild the PCH from the overlay.
- **C4: only the DLL changes.**
  - The built bin must have `legodimensions.exe` and `rexruntime.dll` equal to devoff4b-bin, which build-bin.py checks. TracyClient.dll must also be equal; build-bin.py does not check this, so verify it once by hand.
  - The shared `snap1-sdk/install/bin/rexgpu-xenos.dll` must still be E3CB99CF afterwards (checked at L175).
  - The ON DLL must still export exactly the same 4 names (my `pe_scan.py exports` gives this in one line).
- **C5: needles.**
  - Run with `--want` set to at least one #19 cvar string (`d3d12_async_submit`) and `d3d12_submit_split_kb`. The check is that each string is present in the ON DLL and absent from devoff4b-bin.
  - This shows the patched `command_processor.cpp` is what got linked.
- **C6: the r19-rating (a)/(b)/(c) conditions all still apply** (default OFF, S1 row g before soak e and W7, S2 combination guard). This ruling changes only how the bin is built, not what may be run with it.

## Findings

- **NIT N1: build priority.** `build-bin.py` L96-97 now pass `--priority normal`, where the 02:38 dry run used belownormal, with `--jobs 8`. That is acceptable only if the build finishes well before the 03:40 command cutoff; otherwise go back to belownormal.
- **NIT N2: no TracyClient check.** `build-bin.py` hash-checks the exe and rexruntime but not `TracyClient.dll`; covered by C4.
- **NIT N3: tools still changing.** `build-bin.py` and `recompile.py` were edited after the dry run (02:39 mtime, sizes changed again by 02:42). Record the hashes of the versions that actually run in the bin MANIFEST notes.

## Read / sent

- I read `s33/r19/prep.txt`, `build-bin.txt`, `list-on.tsv` and `replace-on.txt`.
- I read the `build-bin.py` steps and the `relink.py` `pe_compare` and exit codes.
- I checked the `snap1-sdk/compile_commands.json` flags for `command_processor.cpp` Release, and grepped the `#include` forms across snap1 `rexglue-sdk/include` and `src/graphics`.
- Scans (scripts in `agent10/session3/scratch-r19build/`):
  - `ninja_deps_scan.py` over snap1-sdk, snap1-off and snap1-on;
  - `pe_scan.py` exports and imports over devoff4b-bin.
- Sent to the Overseer at 02:43.
