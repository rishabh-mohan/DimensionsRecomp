# FINAL build plan (M2, 2026-11-25). Diff only: nothing is built until the Overseer says so and M10 has rated it

> [!IMPORTANT]
> 07:20 update after M10's rating C20B6FDB (SAFE-IF):
> - The exact commands and STOP gates are in `BUILD-STEPS.md`; it takes precedence over this file.
> - **N-A is confirmed** for native (Overseer 13:01Z).
> - **D4:** shaders.cpp is in the `-fsyntax-only` set. So are all other changed TUs and the OFF-define variants: `final/fsyntax.py`.
> - **D1/S2:** B4 has a CTL leg. The 4 native TUs, unpatched, with fingerprint 9b40, are relinked; the result must equal the native4b exe and map except the TimeDateStamp.
> - **D2:** the "rexruntime extension" is a new driver, `final/build-final.py`, plus `final/prep-final.py`. recompile.py and relink.py are unchanged.

Inputs:
- `build/agent2/final/FINAL-DEFAULTS.diff`, 11 files;
- `DEFAULTS-TABLE.md`;
- `check-defaults.py`;
- `verify-diff.py`;
- `predict-fingerprint.py`.

Base: the snap1 tree that built devoff4b-bin / native4b-bin (`build/agent2/snap1`, S4b). Its 11 before-files are byte-identical to live HEAD. Every build runs from a **fresh copy**. Patch with `git -c core.autocrlf=false apply`. Check the before-hashes first, then the after-hashes == `final/work/new`:

| file | before | after | TU goes to |
|---|---|---|---|
| rexglue-sdk/src/core/clock.cpp | A07EE16C9C5CC4BE | EAE926AC812F7EFD | rexruntime.dll (rexcore OBJECT lib) |
| rexglue-sdk/src/core/timer_queue.cpp | 015C04A22DACC592 | EF70211E5D248A94 | rexruntime.dll (rexcore OBJECT lib) |
| rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp | 8DF708B87A945F07 | CEB5529AC853D5A8 | rexruntime.dll |
| rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp | 6E20D417F0ED93A5 | 7CA55716E7092199 | rexruntime.dll |
| rexglue-sdk/src/system/runtime.cpp | 306B692BC091A56F | A997D0059A69FF99 | rexruntime.dll |
| rexglue-sdk/src/system/xmemory.cpp | BCA5E1CF63686E73 | 3745C04AAC8AF75D | rexruntime.dll |
| rexglue-sdk/src/system/xobject.cpp | 189CA288893B1A36 | 691A34BB64E11EA2 | rexruntime.dll |
| rexglue-sdk/src/system/xthread.cpp | FAEF9B99C893F684 | 3B50A95E76B10377 | rexruntime.dll |
| rexglue-sdk/src/graphics/shared_memory.cpp | A4A31038ABDFF94A | E2465A155E22C20B | rexgpu-xenos.dll |
| rexlego/src/gpu_wait_backoff.cpp (LF) | 01D9F8F3464C8614 | 74115EEA26C4AEB2 (= M9 q500) | Xenos exe only |
| rexlego/src/gpu_native/shaders.cpp (**CRLF**) | 9567FE3F3B63637D | 4B8250E976A38401 | native exe only |

- TU-to-target mapping is from `snap1-sdk/CMakeFiles/impl-Release.ninja`: the rexcore objects link only into rexruntime.dll.
- No header changes, so there is **no PCH impact**, and the import libraries and exports stay the same. The exe does not need a relink for the SDK part.
- The shared_memory.cpp before-hash A4A31038 is the same file the C1 verify fix started from (devoff4bv). The FINAL diff does **not** include the C1 verify fix.

## B1. SDK: new DLL pair (rexruntime.dll + rexgpu-xenos.dll)

- **Method:** the dependency-scoped recompile already used for r19 (`session3/recompile.py`, method `build/agent10/session3/r19-build-method.md`):
  - work in a fresh overlay copy of the 9 SDK files;
  - use the snap1-sdk ccdb, `--include-first` overlay, reuse the existing PCHs unchanged, `--fwd-src`, `-fmacro-prefix-map` overlay→snap1, `--jobs` ≤ 8.
  - The TU set is exactly these 9: cpp-only changes, so ninja deps add nothing.
- **Extension needed:** recompile.py/relink.py were only ever run for the rexgpu-xenos target. The rexruntime.dll target (8 TUs, incl. 2 rexcore objects under `src/core/CMakeFiles/rexcore.dir/`) needs its link rsp. This is a small script change, to be rated with the build.
  - Fallback: a full SDK build in a fresh copy of snap1-sdk (Release, the same configure). This takes longer.
- **CTL leg first, per DLL:** relink with the 9 unpatched TUs recompiled. The result must equal devoff4b-bin's rexruntime.dll / rexgpu-xenos.dll except the TimeDateStamp. Otherwise stop.
- **Output:** a new dir, e.g. `build/agent2/final/sdk-out/`.
  - **Never** write `snap1-sdk/install/bin/rexgpu-xenos.dll` (E3CB99CF; shared by devoff4b-bin, devoff4b-cg26-bin, native4b-bin) or anything else in snap1-sdk/install.
  - After staging, re-verify those 3 MANIFESTs: 0 FAIL.
- **Needles** (build-bin.py `--want`, against the devoff4b DLLs; must be absent there):
  - rexruntime.dll: `Final defaults:{}`;
  - rexgpu-xenos.dll: `Final defaults (GPU): {} {}`.
- **ON exports:** the same names as devoff4b for both DLLs. Use the PE parser in `session3/r19-checks.py`.

## B2. Xenos final bin: `build/agent2/devfinal-bin` (the ship candidate)

- devoff4b-bin with 3 files replaced:
  - rexruntime.dll (B1);
  - rexgpu-xenos.dll (B1);
  - legodimensions.exe, relinked after recompiling `gpu_wait_backoff.cpp` in the devoff4b game tree lineage (`snap1-off`: Release, NATIVE_GPU=OFF, x86-64-v3, LEGO_GPU_WAIT_HOOK_GETDATA=1).
  - TracyClient.dll is unchanged. Check it by hash against devoff4b-bin.
- Exe CTL leg: relinking with the unpatched TU must equal devoff4b's exe except the TimeDateStamp. Otherwise stop.
- q500 compile/bin checks (rating DB5D1282, condition 5):
  - `clang -fsyntax-only` of the TUs that get new code (`gpu_wait_backoff.cpp`, `runtime.cpp`, `shared_memory.cpp`, and **`shaders.cpp`** per D4), each with its own ccdb flags (devoff flags for gpu_wait_backoff, snap1-on flags for shaders.cpp), before the real build. fsyntax.py runs all 11 changed TUs plus the native header users and the OFF defines. Not run yet: compiler processes wait for the Overseer's go.
  - The map's hooked aliases stay at 31.
  - The exe contains the literal `GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=` (the new-bin marker).
  - The native fingerprint is unaffected by q500: the TU is not built in native.
- MANIFEST: sha256 of every file, the FINAL-DEFAULTS.diff sha256, every before/after hash above, the hashes of the tool scripts that ran, and the needle results. No cache/ and no seeds.
- **First run proof:** `python build/agent2/final/check-defaults.py <game.log> --mode xenos` must PASS on a plain launch (no cvars except the bench `framerate_limit=0`, env without any `LEGO_GPU_WAIT_*`). It checks:
  - all 13 keys `(default)` at the win3 values;
  - the 1 ms line, C1 keep-watch on, TimerQueue precise and back-off ON 500/30, once each;
  - no bad strings.
  - Tonight's win3 run passes the same proof lines: `--mode legacy` on `build/agent8/matrix/20261125-0315/runs/0319-win3-r1/game.log` gives PASS.

## B3. Xenos OFF bin (optional): `build/agent2/devfinal-off-bin`

Only if a run needs empty-env OFF semantics on the new code. Build it as B2, but compile `gpu_wait_backoff.cpp` with **`-DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1`** and record the define in the MANIFEST (q500 rating condition 3). The SDK cvars have no OFF define: OFF arms set the 12 old values explicitly (list in DEFAULTS-TABLE.md). The exact old reference stays devoff4b-bin (s0).

## B4. Native final bin: `build/agent2/nativefinal-bin`

- **Exe:** native4b lineage (`snap1-on`, NATIVE_GPU=ON, Agent 6 AOT inputs) with `shaders.cpp` patched.
  - The fingerprint changes `9b40acbbef4c57b3` → `1616ce65e973c583` (predicted). The generated `native_gpu_build_info.h` changes, so `shaders.cpp`, `device.cpp`, `shader_archive.cpp` and `pipeline_library.cpp` recompile, then the exe relinks.
  - Checks:
    - the exe contains the new fingerprint and not the old one;
    - `native-gpu-build.txt` == the prediction;
    - the needle `Native GPU: shader miss cache {} ({}{})` is present in the new exe and absent in native4b's.
  - First launch is cold: old recipes and packs are rejected by fingerprint.
- **CTL leg (D1/S2):** recompile the 4 TUs from the unpatched sources with snap1-on's own header (9b40) and relink. The result must equal native4b-bin's exe, and the map must match except the Timestamp line. Otherwise STOP.
- **SDK choice (open, Overseer/M10 decide):**
  - **N-A (recommended, exactly as timed):** stage the new exe with the **old** snap1-sdk DLLs (copies of native4b-bin's rexruntime.dll and rexgpu-xenos.dll E3CB99CF; never write the source).
    - This is W8a `mc`: native4b + miss cache, every SDK switch off, as timed.
    - Proof: `check-defaults.py --mode native-old`.
  - **N-B:** stage with the B1 DLLs. Native then inherits hold_global_lock, P2 and the d11p timer bundle. keep_watch is blocked in native (`memory_watch.cpp` L33-36 logs "blocked ... (native renderer)").
    - None of this has been timed or functionally tested in native.
    - It needs a functional gate plus at least one timing pair vs N-A before it ships.
    - Proof: `check-defaults.py --mode native`.
  - The ABI is unchanged, so one exe serves both; the choice is staging only.
- **Native OFF bin (optional):** `-DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0`, recorded in the MANIFEST. Otherwise native4b-bin stays the n0 reference.

## Order and time (estimate, all cores, normal priority after go)

1. B1: 9 TUs plus 2 DLL links, CTL then ON. About 5 min, plus the recompile.py rexruntime extension.
2. B2: 1 TU plus the exe relink, CTL then ON. The 170 MB exe link is the long step.
3. B4: 4 TUs plus the native exe relink (315 MB).
4. B3 and the native OFF bin only if asked.

Stage each bin atomically and re-verify the 3 shared-DLL bins after each.

## Harness rules before any run on a new bin (q500 rating condition 4, S1, N1)

- Every new-bin off/ref arm sets `LEGO_GPU_WAIT_BACKOFF_US=off` (lowercase), including STATS-only probe arms. Old-bin arms keep `env {}`.
- New-bin SDK-off arms set the 12 old cvar values explicitly.
- `stage-window.ps1` and the GO checks refuse a new-bin arm that lacks the key, unless it is the named default arm.
- Expect and row-gate rules are per bin: new bins log `Final defaults` lines and the miss-cache line. Old expect files that forbid "GPU wait back-off" do not apply to new bins.
- New-bin matrices name the default arm explicitly. Proof of which arm ran = run.json `env_set` + the bin id (the log line equals env 500), plus `check-defaults.py`.

## Step-B gates on devfinal-bin (q500 rating condition 1; time the shipped combination, condition 2)

1. The loaded-machine arm.
2. A functional pair: default vs `off`.
3. Timed: `off` / default / env 500, ≥ 4 reps × 2 passes, including level frame-time tails.
4. A quiet-host repeat.
5. An f10 quiet pair under the finding-10 rule.
6. The new-PC sweep.

The shipped combination is the full win3 set as defaults, so the timed default arm runs it with no cvars. The ref arm sets the 12 old values plus `off`.

## Stale text left on purpose (q500 rating N2)

- The `gpu_wait_backoff.cpp` header "DRAFT / Syntax-checked only".
- rexlego CMakeLists L181-183 ("Off unless ... set").
- Label notes and bins by whether they include 74115EEA.
