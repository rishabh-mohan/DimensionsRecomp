# native-cpu tools: sampling-profiler analyser

`analyze_profile.py` reads the profiles written by the game's built-in sampling profiler
(`DimensionsRecomp/rexlego/src/sample_profiler.cpp`) and turns them into per-thread,
per-category and per-function reports, folded stacks for flame graphs, and A/B diffs.
It needs Python 3.11+ and the standard library only. If `llvm-undname` is on PATH or in
`toolchain/llvm-*/bin` it is used to demangle C++ names; otherwise a simpler built-in
demangler is used.

| file | purpose |
|---|---|
| `analyze_profile.py` | the analyser (single file, stdlib only) |
| `run_selftest.ps1` | builds `selftest/profiler_selftest.cpp` together with the unchanged `sample_profiler.cpp`, profiles a known workload, and checks the analyser's output |
| `selftest/profiler_selftest.cpp` | self-test workload: hot loop, fake guest function + hook, waiting threads |
| `selftest/map_hooks.py` | self-test helper: lists the map entries the analyser derives for one guest address |

`check_saverest.py` and `gen_lock_elide.py` are separate tools and are not covered here.

## 1. Capturing a profile

| what | how |
|---|---|
| enable | set `LEGO_SAMPLE_PROFILE` **before the process starts**. The variable only has to exist (`getenv != nullptr`), so even `LEGO_SAMPLE_PROFILE=0` turns profiling on. A static initializer starts the sampler thread when the exe loads. |
| record (by hand) | press **F9** to start recording and press it again to stop. |
| record (scripted) | set `LEGO_SAMPLE_PROFILE_TRIGGER=<file path>`. The sampler records while that file exists and writes the profile when the file is deleted. |
| output | `profile-<GetTickCount64()>.bin` in the exe's directory |
| symbols | the exe links with `/MAP:legodimensions.map`. Use the map from the **same build** as the exe that wrote the profile. |

Timing notes for the trigger file:
- While idle, the sampler checks for the file every 50 ms. Before recording it plays `Beep(440,150)`, which blocks the sampler thread. **Recording therefore starts about 150-200 ms after the trigger file appears.** `--trigger-latency` (default 0.175 s) subtracts this from a trigger window read with `--meta`.
- After writing the profile the sampler plays `Beep(880,150)`. Wait until the `.bin` file exists and its size stops changing before reading it (the self-test does this).

What one sampler round does: it takes a `CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD)` (this snapshots all threads on the system), then, for every other thread in the process, it calls `SuspendThread`, then `GetThreadContext`, then walks up to **24 frames** with `RtlLookupFunctionEntry`/`RtlVirtualUnwind` (a frame without unwind info uses `[Rsp]` as the return address), then `ResumeThread`. It then waits about 1 ms:
- **Current sampler:** a high-resolution waitable timer (`timer_mode 1` in the trailer). This does not change the process-wide timer resolution.
- **Legacy sampler, and fallback before Windows 10 1803:** `timeBeginPeriod(1)` held for the whole process lifetime, plus `Sleep(1)` (`timer_mode 0`). This makes every guest `Sleep()` about 1 ms granular. That is an **observer effect**: use such profiles for attribution only, not for timing. The analyser prints `sampler held timeBeginPeriod(1): ...` in every report header for these profiles (and for every profile without a trailer).

The real sampling rate is below 1 kHz, because each round pays for the snapshot plus a suspend/resume per thread. It **drops sharply when the machine is CPU-saturated**: `GetThreadContext` waits until each suspended target thread has actually been scheduled. The self-test saw 3-5 rounds/s while other builds kept all 12 logical CPUs at 100%. The analyser warns when the rate is below 250 rounds/s. Even then, attribution percentages stay usable, but they are based on few samples. For timing A/B runs, turn the profiler **off**.

## 2. File format (little-endian)

```
"LSP1"
u32 module_count
  per module: u64 base, u32 size_of_image, u32 name_len, name bytes (base name, e.g. "ntdll.dll")
u64 sample_count
  per sample: u32 tid, u32 depth, u64 frames[depth]   (frames[0] = leaf RIP, then return addresses)
optional trailer (newer sampler):
"LSPX"
u32 version            (1)
u32 payload_bytes      (bytes after this field; readers always use it to bound/skip the block)
payload v1:
  u64 qpc_frequency, u64 qpc_start, u64 qpc_end, u64 rounds,
  u32 timer_mode       (0 = timeBeginPeriod(1)+Sleep(1), 1 = high-resolution waitable timer)
  u32 thread_count
  per thread: u32 tid, u32 name_bytes, UTF-8 name (GetThreadDescription; may be empty)
```

Later versions only append fields to the payload. The analyser reads the v1 fields and reports any extra bytes as `extra_payload_bytes`. Problems produce a warning, never an error:
- A trailer that is truncated, too small or implausible is ignored.
- Unknown bytes after the samples or after the LSPX block are ignored.
- A file with no trailer (the legacy sampler) gets `timer_observer_effect: true`, rates per 1000 rounds unless you give a duration, and no thread names.

## 3. Using the analyser

```powershell
$a = 'DimensionsRecomp\tools\native-cpu\analyze_profile.py'
python $a profile-123.bin legodimensions.map                 # summary: threads, categories, top 25 self/inclusive
python $a profile-123.bin                                    # map defaults to <exe>.map or legodimensions.map next to the .bin
python $a p.bin game.map --by module                         # adds per-module self/inclusive tables
python $a p.bin game.map --thread 1234 --thread 0x4d2        # only these threads
python $a p.bin game.map --focus 'sub_8212ABCD|DrawIndexed'  # callers/callees of matching functions (regex on display + raw name)
python $a p.bin game.map --fold-guest                        # merge consecutive guest frames into "guest [folded]"
python $a p.bin game.map --include-waits                     # count waiting/io samples too (default: busy only)
python $a p.bin game.map --folded > out.folded               # root->leaf folded stacks (add --folded-thread for a thread prefix)
perl flamegraph.pl out.folded > flame.svg                    # Brendan Gregg's FlameGraph, not included here
python $a p.bin game.map --json -o report.json               # machine-readable; -o works for every mode
python $a p.bin game.map --duration-s 30                     # duration for legacy files without a trailer
python $a p.bin game.map --meta run-meta.json                # ... or from harness metadata
python $a --diff A.bin A.map B.bin B.map                     # per-function delta in samples/s (or per 1k rounds)
python $a --diff A.bin A.map B.bin B.map --duration-a 30 --meta-b runB.json
```

More options:
- `--top N` sets the number of rows (default 25).
- `--keep-params` keeps C++ parameter lists.
- `--no-undname` uses only the built-in demangler.
- `--map MODULE=PATH` adds a map for another module (e.g. a rexruntime DLL).
- DLL symbols come from the export tables and `.pdata` of the DLL files on disk. The search order is `--bin-dir` (default: the profile's directory), then `--search DIR` (repeatable), then `System32`, then, with `--driverstore`, `System32\DriverStore\FileRepository` (for GPU user-mode drivers; a matching `SizeOfImage` is preferred).

**Duration** (for per-second rates). The first available source wins:
1. The LSPX trailer: `(qpc_end - qpc_start) / qpc_frequency`.
2. `--duration-s SECONDS`.
3. `--meta FILE`, a JSON object, searched at the top level and one level deep:
   - `duration_s` (number of seconds), or
   - `profile_trigger_start` + `profile_trigger_end`, or `trigger_start` + `trigger_end`. Each value is epoch seconds (a number) or an ISO-8601 string; a string without a time zone is read as local time. The window minus `--trigger-latency` is used.
4. Otherwise rates are per 1000 sampler rounds, with a warning. Rounds come from the trailer or are estimated as the largest per-thread sample count.

For `--diff`, use `--duration-a/--duration-b` and `--meta-a/--meta-b`; the same priority applies.

### How samples are attributed

- **Return addresses.** `frames[0]` is looked up as-is. Return addresses are looked up as `addr - 1`, so a call in the last bytes of a function is attributed to that function and not to the next one.
- **Main exe** (lld map):
  - The analyser builds a sorted table from the map's `Publics by Value` and `Static symbols` sections (RVA = `Rva+Base` minus the preferred load address) and looks addresses up with bisect.
  - Only sections of class `CODE` are used; LLD maps have no `f` function flag. Data, absolute (`0000:`) and linker-defined symbols are ignored, and an address outside the CODE ranges is `unknown`.
  - Several names at one address (ICF): one name is shown, preferring `sub_X`, then public over static, then non-thunk, then the shortest. The rest are shown as `{+N aliases}`.
- **Guest code.**
  - The codegen (`rexglue-sdk`, `function_graph.cpp`) names a guest function `sub_%08X`. `pch_h.inja` emits the body as `__imp__sub_X` and `sub_X` as a weak alias at the same address. The analyser shows `sub_X [guest 0xX]`.
  - A **hook** is a strong `sub_X` (`REX_HOOK_RAW`) at a different address from `__imp__sub_X`. It is shown as `sub_X [hook of guest 0xX]` and categorised as host code (`rexlego`). The original body is shown as `__imp__sub_X [guest 0xX, hooked original]`.
- **Other modules**: export names plus `.pdata` function starts. Internal functions appear as `fn_<RVA> (near Export+0xOFF)`. If the DLL on disk has a different `SizeOfImage` from the loaded one, a warning says the names may be wrong.
- **Leaf classification** (`LEAF_CLASS_RULES` at the top of the script):
  - `wait`: the leaf is an ntdll/win32u wait syscall stub, e.g. `NtWaitForSingleObject`, `NtDelayExecution`, `NtRemoveIoCompletion`, `NtWaitForWorkViaWorkerFactory`, `NtUserMsgWaitForMultipleObjectsEx`, the D3DKMT wait stubs.
  - `io`: synchronous I/O stubs.
  - Everything else is `busy`.
  - By default only busy samples are counted in the function tables. The per-thread table always shows busy/wait/io. A waiting thread's "role" is its leaf-most guest/rexlego/native-gpu/rexruntime frame.
- **Categories** (`CATEGORY_RULES`, first match wins; the category of the leaf frame decides):
  - `guest`: `sub_X`/`__imp__sub_X`, or an object `*_recomp.N.cpp.obj`.
  - `native-gpu`: `@gpu_native@` in the mangled name, or an object whose basename matches a file in `rexlego/src/gpu_native/*.cpp`.
  - `rexlego`: any other symbol of the main exe, including hooks.
  - `rexruntime`: `rexruntime*.dll`.
  - `d3d12+driver`: d3d12/dxgi/dxcore, the NVIDIA/Intel/AMD user-mode drivers, `win32u!NtGdiDdDDI*`, `gdi32!D3DKMT*`.
  - `system`: any DLL that also exists in System32, plus the CRT DLLs.
  - `other`: any other module.
  - `unknown`: an address in no module, or outside the exe's code ranges.

### JSON (schema 1) keys for harnesses

Summary:
- `samples`, `threads_seen`, `modules`, `counting`, `counted_samples`, `thread_filter`, `fold_guest`.
- `timer_observer_effect`: true / false / "unknown".
- `trailer`: null, or version, payload_bytes, qpc_*, rounds, timer_mode, thread_count, thread_names{tid: name}, extra_payload_bytes.
- `duration`: seconds, source, rounds, rounds_estimated, rounds_per_s.
- `rate_unit`: `/s` or `/1k rounds`.
- `totals`: busy/waiting/io.
- `categories_busy`.
- `threads[]`: tid, name, samples, busy, waiting, io, pct_running, top_self[], top_inclusive[], role.
- `top_self[]` and `top_inclusive[]`: name, category, module, guest_addr, kind, samples, pct, rate.
- `modules_self` / `modules_inclusive` (with `--by module`).
- `focus` (with `--focus`).
- `timing`, `map_info`, `warnings`.

Diff: `unit`; `a`/`b` (profile, map, samples, duration, timer_observer_effect); `categories[]`, `self[]` and `inclusive[]` (name, a, b, delta, delta_pct, a_samples, b_samples); `max_abs_delta_self`; `warnings`.

Folded with `--json`: `stacks[]` (stack, count), `timer_observer_effect`, `warnings`.

## 4. Self-test

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File DimensionsRecomp\tools\native-cpu\run_selftest.ps1 [-Rebuild] [-Seconds 3]
```

- **Build.** The script dot-sources `env\devshell.ps1` and builds into `build\agent8\profiler\` with one sequential clang-cl per file and `lld-link /threads:1 /MAP`. It rebuilds only when the sources changed.
- **Run.** It runs the exe with `LEGO_SAMPLE_PROFILE` and a trigger file and copies the profile to `bench\agent8\profiler\selftest-<stamp>.bin`.
- **Analyse.** It runs the analyser in every mode and checks:
  1. the main thread's busy leaf is `lsp_selftest_hot` (>= 80%);
  2. the guest thread's busy leaf is `sub_8200BEEF [guest 0x8200BEEF]`, category guest (>= 80%), and the map yields the hook / hooked-original pair for `0x8200CAFE`;
  3. the threads blocked in `WaitForSingleObject` and `Sleep(20)` are >= 90% waiting, with roles `selftest::Waiter` / `selftest::Sleeper`;
  4. `lsp_selftest_outer` is inclusive for >= 80% of main busy samples, and `--focus` names it as the caller;
  5. `--folded`, `--by module`, `--fold-guest` and `--diff` (self vs self = 0) work;
  6. when `sample_profiler.cpp` writes LSPX: the trailer parses, timer_mode 1, rounds > 0, duration > 0, and the thread names `selftest-main/-guest/-waiter/-sleeper` map to the right tids.
- **Results.** Written to `bench\agent8\profiler\selftest-latest.txt`. The exit code is 1 on FAIL.

Synthetic tests (no game data) and the 1M-sample timing: `python bench\agent8\profiler\synth_test.py` (`--skip-big` skips the timing run).

## 5. Limitations

- **Stack depth.** Stacks are capped at 24 frames by the sampler, so deep call chains are cut at the root end.
- **System DLL names.** Names inside system DLLs are only as good as exports + `.pdata` allow: internal functions show as `fn_<rva> (near X+off)`. The DLL files on disk must be the versions that were loaded (the `SizeOfImage` check catches most mismatches).
- **Thread names** need the LSPX trailer, so legacy profiles have none.
- **Map matching.** The map must come from the same build as the exe. Nothing checks this beyond module-name matching; a stale map produces plausible but wrong names.
- **Guest detection** relies on the `sub_X` naming or `*_recomp.N.cpp.obj` objects. Guest functions renamed through codegen config are caught only by the object rule. gpu_native detection matches object basenames, because the map has no paths.
- **Hooks** count as host code (`rexlego`), not as guest.
- **Low sampling rate.** On a busy machine the rate collapses (see section 1), so check `duration.rounds_per_s`.
