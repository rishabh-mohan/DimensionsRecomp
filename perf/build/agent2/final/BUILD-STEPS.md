# FINAL-DEFAULTS build steps (M2, 2026-11-25)

Rating: M10 `final-defaults-rating.md` (C20B6FDB), SAFE-IF D1-D7 + F1-F7. N-A for native (Overseer 13:01Z).

Do not start until the Overseer says go.
- Run every command from the WS root `<workspace>`, in PowerShell.
- Normal priority. recompile.py runs at most 8 jobs (`--jobs` ≤ 8). Links run one at a time.
- Every script refuses to start while `perf-notes\WINDOW-HOLD.txt` exists, and kills its compiles or links if the file appears.

## Hard rules (every step)

- **Write only `build\agent2\final\b\` and the new `build\agent2\<name>-bin\` dirs.**
  - snap1, snap1-sdk, snap1-off and snap1-on are read-only inputs.
  - relink.py writes only into its `--out-dir`.
  - recompile.py writes only the listed objects, and refuses `-MF/-MD/-MMD/-MT/-MQ`.
- **D6:** never write `build\agent2\snap1-sdk\install\` (the shared `rexgpu-xenos.dll` E3CB99CF) or any staged bin. Never run `cmake --install`.
  - Stage only with `stage-variant.py`. It builds a `.tmp` dir, then renames it, so the stage is atomic.
  - After each staging, `verify-bins.py` must show 0 FAIL on the new bin and on devoff4b-bin, devoff4b-cg26-bin and native4b-bin.
- **A STOP gate failing means: stop, stage nothing, report to the Overseer.** Do not work around a gate.
- Each script writes its log and ends with `RESULT: PASS|FAIL`:
  - `b\prep.txt`;
  - `b\fsyntax\fsyntax.txt`;
  - `b\<leg>\build-final.txt` + `notes.txt`;
  - `b\stage-<bin>\build-final.txt`.

## Tools (sha256/16, as of this file; build-final.py logs the hashes that actually ran into every MANIFEST note)

| tool | role |
|---|---|
| `build\agent2\recompile.py` 855BCC79148E2DA8 | unchanged; recompiles listed TUs with the ccdb's own command |
| `build\agent2\relink.py` F3C6EEAF332AB213 | unchanged; reruns one ninja link edge with objects swapped; `--compare` (TimeDateStamp only), `--compare-map` |
| `build\agent2\stage-variant.py` D2BD1C6358FC19C1 | unchanged; atomic staging + MANIFEST |
| `build\agent2\session3\verify-bins.py` 80FF4C5F581C4B1B | unchanged; MANIFEST re-verify |
| `build\agent2\s4b\mapcheck-s4c.py` F8CB7B495F74D978 | unchanged; hooked aliases by name/object |
| `final\prep-final.py` | step 0 |
| `final\fsyntax.py` | step 1 (D4) |
| `final\build-final.py` | legs + stage: **the rexruntime extension (D2)** |
| `final\pe-check.py` | D5 |
| `final\pe-diff.py` | D3 (fallback only) |

**D2 (the rexruntime extension) needs no diff to recompile.py or relink.py.** Both already take any ccdb, ninja file and `--target`. build-final.py points them at the rexruntime.dll edge:
- the target is `build/agent2/snap1/DimensionsRecomp/rexglue-sdk/out/win-amd64/Release/rexruntime.dll`;
- relink.py reads that edge from `snap1-sdk\build-Release.ninja`, which includes `CMakeFiles\impl-Release.ninja`;
- the 8 objects swapped include the 2 rexcore.dir objects: `src/core/CMakeFiles/rexcore.dir/Release/{clock,timer_queue}.cpp.obj`;
- relink.py fails if an object to swap is not exactly one explicit input of that edge;
- the link rsp it used is saved in `b\rt\link-*\relink-rsp-content.txt`.

The rexruntime CTL leg (step 2, gate D1) is the proof.

## Step 0: prep (no compiler; runs ninja `-t deps`, `cmake -P`, git apply; hashes the 315 MB exes)

```powershell
python build\agent2\final\prep-final.py --dry-run
python build\agent2\final\prep-final.py
```

**STOP gates** (prep-final RESULT must be PASS):
- FINAL-DEFAULTS.diff sha256 starts with 955543F5 and names exactly the 11 files.
- The shared DLL is E3CB99CF.
- The 11 snap1 before-hashes match.
- snap1-off exe+map == the devoff4b-bin MANIFEST rows; snap1-on exe+map == native4b-bin's.
- The native TU set from `ninja -t deps` (objects including `native_gpu_build_info.h`, plus shaders.cpp) == {shaders, device, shader_archive, pipeline_library}.
- The overlay copy == snap1, byte for byte.
- `git -c core.autocrlf=false apply --check`, then apply: exit 0, 11 "Checking patch", 0 skipped.
- 11 after-hashes == the BUILD-PLAN table and == `final\work\new`. Line endings are kept: shaders.cpp CRLF, the rest LF.
- Fingerprint, from snap1-on's own `generate-native-gpu-fingerprint.cmake` run on copies with `cmake -P`:
  - gen-ctl == the snap1-on header and native-gpu-build.txt, byte for byte;
  - gen-on has `1616ce65e973c583` and equals the old header with only the fingerprint swapped.

## Step 1: `clang -fsyntax-only` (D4; first compiler processes)

```powershell
python build\agent2\final\fsyntax.py --dry-run
python build\agent2\final\fsyntax.py
```

**STOP gate:** every TU exits 0 with 0 errors. Each TU uses its own ccdb flags and the same flags as its ON leg: prefix map, `--include-first`, defines. It writes nothing outside `b\fsyntax\`. Warnings are listed in the log, not gated. The set, 19 commands:
- `rt`: the 8 SDK TUs (clock, timer_queue, xboxkrnl_rtl, xboxkrnl_threading, runtime, xmemory, xobject, xthread), snap1-sdk flags.
- `gpu`: shared_memory.cpp, snap1-sdk flags.
- `xe`: gpu_wait_backoff.cpp, snap1-off flags. `xeoff`: the same plus `-DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1`.
- `nat`: **shaders.cpp** plus device, shader_archive and pipeline_library, snap1-on flags, with `-I b\nat\gen-on` first. `natoff`: the same plus `-DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0`.

## Step 2: B1 SDK legs (rexruntime.dll, rexgpu-xenos.dll)

```powershell
python build\agent2\final\build-final.py --leg rt --dry-run
python build\agent2\final\build-final.py --leg rt
python build\agent2\final\build-final.py --leg gpu --dry-run
python build\agent2\final\build-final.py --leg gpu
```

The CTL step recompiles the leg's unpatched snap1 TUs and relinks.

**STOP gates (rt):**
- **D1 CTL:** the CTL relink == devoff4b-bin `rexruntime.dll` A33801D1, except the TimeDateStamp.
- `Final defaults:{}` is in ON and not in devoff4b's DLL.
- No `agent2/final/b/` path bytes in the output.
- No pch or error text in any compile log.
- **D5:** exports == devoff4b's (10467); every import table unchanged.
- The shared DLL is E3CB99CF before and after.

**STOP gates (gpu):**
- **D1 CTL:** the CTL relink == devoff4b-bin `rexgpu-xenos.dll` E3CB99CF, except the TimeDateStamp.
- `Final defaults (GPU): {} {}` is in ON and not in devoff4b's DLL.
- **D5:**
  - exports == devoff4b's (4);
  - imports from rexruntime.dll == the ref's 115, plus exactly 2 added names, matching `GetFlagByName` and `GetFlagSource`;
  - both added names are exports of devoff4b's rexruntime.dll;
  - every other DLL's imports are unchanged.
- The shared DLL is E3CB99CF before and after.

## Step 3: B2 Xenos exe (gpu_wait_backoff.cpp, snap1-off lineage)

```powershell
python build\agent2\final\build-final.py --leg xe --dry-run
python build\agent2\final\build-final.py --leg xe
```

**STOP gates:**
- **D1 CTL:** the exe == devoff4b-bin `legodimensions.exe` DFBE1D43, except the TimeDateStamp, and the map == devoff4b's except the Timestamp line.
- The q500 marker `GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=` is in ON and not in devoff4b's exe.
- The miss-cache needle is absent.
- **D5:** the import table and exports == devoff4b's exe.
- mapcheck `--mode s4c` vs devoff4-bin's map: the 31 hooked aliases.
- No overlay path bytes in the exe or map.
- No pch or error text in the logs.

## Step 4: B4 native exe (N-A; shaders.cpp + the 3 header users, snap1-on lineage)

```powershell
python build\agent2\final\build-final.py --leg nat --dry-run
python build\agent2\final\build-final.py --leg nat
```

**STOP gates:**
- **D1 B4 CTL:** the 4 TUs, recompiled from the unpatched sources with snap1-on's own fingerprint header 9b40acbbef4c57b3, plus a relink, == native4b-bin `legodimensions.exe` except the TimeDateStamp, and the map == native4b's except the Timestamp line.
- The ON exe has `1616ce65e973c583` and `Native GPU: shader miss cache {} ({}{})`. native4b's exe lacks both and has 9b40.
- The ON exe has no `9b40acbbef4c57b3` and no q500 marker.
- `-I b\nat\gen-on` is ahead of `snap1-on/generated` in all 4 commands.
- **D5:** imports and exports == native4b's exe.
- mapcheck `--mode same` vs native4b's map.
- No overlay path bytes.

## Step 5: stage (atomic; D6 re-verify after each)

```powershell
python build\agent2\final\build-final.py --stage devfinal --dry-run
python build\agent2\final\build-final.py --stage devfinal
python build\agent2\final\build-final.py --stage nativefinal --dry-run
python build\agent2\final\build-final.py --stage nativefinal
```

- **devfinal-bin** = devoff4b-bin + rexruntime.dll (rt) + rexgpu-xenos.dll (gpu) + legodimensions.exe/.map (xe).
  - TracyClient.dll == devoff4b's.
- **nativefinal-bin (N-A)** = native4b-bin + legodimensions.exe/.map (nat) only.
  - rexruntime.dll == A33801D1, rexgpu-xenos.dll == E3CB99CF, TracyClient.dll == native4b's.
  - The `native-gpu-build.txt` text (1616ce65e973c583) goes in the MANIFEST note. The file itself is not staged, because native4b-bin has none.

**STOP gates (each bin):**
- every leg in the bin is RESULT: PASS;
- the bin dir is new;
- the stage is atomic;
- **D6:** `verify-bins.py` 0 FAIL on the new bin + devoff4b-bin, devoff4b-cg26-bin and native4b-bin, and the shared DLL is still E3CB99CF;
- no `cache/` in the bin.

Each MANIFEST holds:
- sha256 of every file;
- the FINAL-DEFAULTS.diff sha256;
- the prep before/after lines;
- the CTL compare lines;
- the ON object hashes;
- the needles;
- the D5 and mapcheck results;
- the defines (OFF bins);
- the hashes of the tools that ran.

## Optional OFF bins (only if a run needs them; q500 rating condition 3)

```powershell
python build\agent2\final\build-final.py --leg xeoff           # needs xe's CTL PASS; -DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1
python build\agent2\final\build-final.py --stage devfinal-off
python build\agent2\final\build-final.py --leg natoff          # needs nat's CTL PASS; -DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0
python build\agent2\final\build-final.py --stage nativefinal-off
```

The gates are the same as for xe/nat.
- Also: the OFF exe != the default exe, which shows the define took effect.
- The define is recorded in the MANIFEST.
- natoff keeps the fingerprint 1616ce65e973c583: same sources, only a define differs.

## D3 fallback: full SDK build (only if step 2's CTL fails because of the method, and only after M10 rates the configure delta)

Run it in a fresh copy: `build\agent2\final\fb\`.

1. Copy `build\agent2\snap1\DimensionsRecomp\rexglue-sdk` to `final\fb\DimensionsRecomp\rexglue-sdk`, without its `out\` dir. Verify the copy by hash.
2. Configure exactly like snap1-sdk, from the copy's source dir. Run `. .\env\devshell.ps1` first.
   - `cmake --preset win-amd64 -B build\agent2\final\fb\sdk -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DREXGLUE_BUILD_TESTS=OFF`
   - `-DCMAKE_INSTALL_PREFIX=<WS>/build/agent2/snap1-sdk/install`: the same string as snap1-sdk, in case it is baked in. **`cmake --install` is never run**, so nothing is written there.
   - **Configure delta, needs a rating:** `"-DCMAKE_C_FLAGS=-march=x86-64-v2 -fmacro-prefix-map=<WS>/build/agent2/final/fb/DimensionsRecomp=<WS>/build/agent2/snap1/DimensionsRecomp"`, and the same for `CMAKE_CXX_FLAGS`. This makes `__FILE__` strings name snap1, as they do in the reference.
3. Build: `cmake --build build\agent2\final\fb\sdk --config Release -j 16`. The DLLs land in `fb\DimensionsRecomp\rexglue-sdk\out\win-amd64\Release\`.
4. **D3 STOP gate:** `python build\agent2\final\pe-diff.py <fb DLL> build\agent2\devoff4b-bin\<dll>`, for rexruntime.dll and for rexgpu-xenos.dll.
   - It lists every differing byte range.
   - Allowed: TimeDateStamp and debug-directory fields only. (devoff4b's DLLs have no debug directory.)
   - Otherwise STOP. Never ship fallback DLLs whose unpatched leg has not reproduced the reference.
5. Apply only the 9 SDK files of the diff to the copy:
   - `git -c core.autocrlf=false apply --include=DimensionsRecomp/rexglue-sdk/* ...`, from `final\fb`, with `GIT_CEILING_DIRECTORIES`.
   - Check the after-hashes against the table.
   - Build incrementally (step 3).
6. Run the step 2 checks by hand (needles and `pe-check.py` with the same arguments as build-final's rt/gpu legs). Then copy the 2 DLLs to `b\rt\link-on\` and `b\gpu\link-on\`, and write a PASS log there before `--stage devfinal`.
   - This is a manual path. Report it to the Overseer first.

## D7 harness rules: install before the first run on any new bin (not a build step; Overseer/M3)

- New-bin off/ref arms set `LEGO_GPU_WAIT_BACKOFF_US=off` (lowercase) plus the 12 old cvar values (DEFAULTS-TABLE.md).
  - This includes STATS-only probe arms.
  - Old-bin arms keep `env {}`.
- `stage-window.ps1` and the GO checks refuse a new-bin arm without the key, unless it is the named default arm.
- Expect files are per bin. New bins log the `Final defaults` lines and the miss-cache line. Old "no GPU wait back-off" expects do not apply to new bins.
- Every new-bin matrix names its default arm. Proof of the arm = run.json `env_set` + the bin id + `check-defaults.py`.

## Post-build functional set F1-F7 (before any confirmation window; rating C20B6FDB)

| # | bin | run | pass |
|---|---|---|---|
| F1 | devfinal | plain launch on the WC light route: cvars only `framerate_limit=0`; run.json `env_set` without any `LEGO_GPU_WAIT_*` | `python build\agent2\final\check-defaults.py <game.log> --mode xenos` PASS. This requires the full back-off line, including `; stats OFF; GetData hook built.`. Clean run: no WER, no dialogs, clean exit; bin id in run.json |
| F2 | devfinal | level-l with toypad, ≥ 10 min | clean, 0 bad strings, the C1 line once, no stale-protection recovery |
| F3 | devfinal | OFF arm: 12 old values + `LEGO_GPU_WAIT_BACKOFF_US=off` | `--mode off` PASS |
| F4 | devfinal (optional) | explicit env 500 | the same proof lines as F1 (documents q500 R3) |
| F5 | nativefinal | W8a route | `--mode native-old` PASS (also forbids the `Final defaults (GPU):` line, N3); the fingerprint 1616ce65e973c583 is in the exe and in native-gpu-build.txt; the MANIFEST has rexruntime A33801D1 and rexgpu E3CB99CF; shader-miss warnings ≤ a native4b n0 run on the same route; a 2nd launch in the same dir loads the recipes the 1st saved |
| F6 | nativefinal | `LEGO_NATIVE_SHADER_MISS_CACHE=0` | the line reads `OFF (LEGO_NATIVE_SHADER_MISS_CACHE set)` |
| F7 | nativefinal | level route | clean |

## Report (per bin, to the Overseer)

- the path and the MANIFEST sha256;
- the exe and DLL hashes;
- the CTL compare lines;
- the needles;
- D5;
- mapcheck;
- the D6 re-verify;
- compile and link times. These come from `b\<leg>\build-final.txt` "times" and `b\stage-<bin>\build-final.txt`.
