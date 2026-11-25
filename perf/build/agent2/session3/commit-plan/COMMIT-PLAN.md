# COMMIT-PLAN: final defaults + #33 opt-in (M2, 2026-11-25 15:5x)

**Read-only plan.** Nothing has been applied or committed, and nothing built. Both repos were left exactly as found (`git status` before and after: superproject ` m rexglue-sdk`, ` M thirdparty/plume`; SDK ` ? thirdparty/fmt`, ` m thirdparty/simde`).

**The user's decision:**
- win3 + native miss cache are the shipped defaults (FINAL-DEFAULTS.diff 955543F5).
- CG26 stays OFF.
- #33 `d3d12_pipeline_creation_no_wait` is a suggested opt-in, default OFF.

**Live trees:**

| repo | branch | HEAD |
|---|---|---|
| `DimensionsRecomp` | perf/opt | c9e215f |
| `DimensionsRecomp/rexglue-sdk` | perf/opt | 5350b1d |

The superproject's gitlink is already at 5350b1d.

> [!WARNING]
> **The #33 patch to commit is M6's `build/agent6/s33-popin/s33-popin-nohunk5.patch` (sha256 57CFA8AD…), not `build/agent2/session3/s33-popin-no5.patch` (4061ED2D…).**
> - `devoff4b-s33-bin`, the bin the #33 rows ran on, was built from 57CFA8AD. Its MANIFEST line 1 says so, and its 4 recorded after-hashes match 57CFA8AD applied to live 5350b1d (§3).
> - 4061ED2D gives the same bytes in 3 of the 4 files. In `include/rex/graphics/d3d12/pipeline_cache.h` it lacks a 3-line comment above `AwaitPipelineCreation()` ("Call it only from the thread that drives pipeline creation … the completion event has one waiter."). The difference is comment-only, but the header lines after L68 shift by 3, so 4061ED2D is not byte-equal to what was timed.
> - M10's rating for this patch: `build/agent10/session3/r33-nohunk5-diagd.md`.

## 1. Hunks → repo, file list per repo

`FINAL-DEFAULTS.diff` has WS-root paths (`DimensionsRecomp/...`). `split-final.py` splits it into two repo-relative patches. Only the `diff --git`/`---`/`+++` header lines change; line counts are equal and the check PASSes.

| patch | sha256 (16) | repo | apply from |
|---|---|---|---|
| `final-sdk.diff` | CEEF11E58CE60A3F | rexglue-sdk | `DimensionsRecomp\rexglue-sdk` |
| `final-super.diff` | 3AAEEB9F5BFC33A1 | superproject | `DimensionsRecomp` |
| `s33-popin-nohunk5.patch` (M6) | 57CFA8ADF1E90079 | rexglue-sdk | `DimensionsRecomp\rexglue-sdk` |

Full sha256 values:
- final-sdk CEEF11E58CE60A3F72A2B4DBA0BC1EDEB9930738E2DB9FA157EF1728D16E2660
- final-super 3AAEEB9F5BFC33A14F1C0C108571F7E39C07FB793A19CB8F6390F1CB522AE71B
- nohunk5 57CFA8ADF1E9007954063A87F406056BB137E2D2D8F2484940BD4E1ABF3704AF

### rexglue-sdk: 13 files (9 FINAL + 4 #33, disjoint)

| file | patch | hunks (old line) | what | before → after (sha256/16) |
|---|---|---|---|---|
| src/core/clock.cpp | FINAL | @@-23 | `clock_lockfree` → true | A07EE16C → EAE926AC |
| src/core/timer_queue.cpp | FINAL | @@-26 | `timer_queue_precise_wait` → true; comment | 015C04A2 → EF70211E |
| src/graphics/shared_memory.cpp | FINAL | @@-24, @@-47, @@-66 | `shared_memory_single_hold_rearm` → true (P2); comment; `Final defaults (GPU):` log line in `InitializeCommon` | A4A31038 → E2465A15 |
| src/kernel/xboxkrnl/xboxkrnl_rtl.cpp | FINAL | @@-48 | `cs_spin` → true | 8DF708B8 → CEB5529A |
| src/kernel/xboxkrnl/xboxkrnl_threading.cpp | FINAL | @@-46 | `spinlock_pause_spin` → true | 6E20D417 → 7CA55716 |
| src/system/runtime.cpp | FINAL | @@-35, @@-52, @@-143 | `host_timer_resolution_ms` 0 → 1, `host_timer_throttling_optout` → true; `Final defaults:` log helper; call in `Runtime::Setup` | 306B692B → A997D005 |
| src/system/xmemory.cpp | FINAL | @@-42 | `physical_protect_hold_global_lock` → true (fix (i)), `physical_protect_keep_watch` → true (C1 v3); comments | BCA5E1CF → 3745C04A |
| src/system/xobject.cpp | FINAL | @@-32 | `wait_timeout_round_up` → true | 189CA288 → 691A34BB |
| src/system/xthread.cpp | FINAL | @@-52 | `precise_guest_sleep` → true, `tls_bounds_fix` → true | FAEF9B99 → 3B50A95E |
| include/rex/graphics/d3d12/pipeline_cache.h | #33 | @@-64, @@-430 | `AwaitPipelineCreation()`, `IsCreationNoWait()`, member `creation_no_wait_` (**class layout change**) | 9322AD37 → 0BAF28BE |
| src/graphics/d3d12/command_processor.cpp | #33 | @@-293, @@-2754 | slow-frame report: `dropped draws`, `forced pipeline waits`; IssueDraw skip/await logic | 027204B5 → 00EA93D3 |
| src/graphics/d3d12/pipeline_cache.cpp | #33 | @@-59, @@-166, @@-749, @@-792 | cvar `d3d12_pipeline_creation_no_wait` (default false, kRequiresRestart); latch in Initialize; await in ShutdownShaderStorage; EndSubmission → `AwaitPipelineCreation()` | DA777443 → C4CB51CC |
| src/graphics/frame_stats.h | #33 | @@-30 | `kDroppedDraw`, `kPipelineAwait` ids | EFA82A7C → 9F3C4F9D |

**#33 headers:**
- `pipeline_cache.h` and `frame_stats.h` are not included anywhere in `rexlego/` or `tools/` (`git grep`, superproject). The layout change stays SDK-internal; the 10 TUs that use the header are all in `rexgpu-xenos` (ninja deps, as built for devoff4b-s33).
- `frame_stats.h` is under `src/`, so it is private.

### superproject (DimensionsRecomp): 2 files + gitlink

| file | hunks (old line) | what | before → after |
|---|---|---|---|
| rexlego/src/gpu_wait_backoff.cpp | @@-15, @@-69, @@-88, @@-97, @@-116, @@-131, @@-142 | q500: back-off default 500 us (`LEGO_GPU_WAIT_BACKOFF_DEFAULT_US`, `-1` = OFF build); `off` value; M9 q500-default.diff 28F0D1DE verbatim | 01D9F8F3 → 74115EEA |
| rexlego/src/gpu_native/shaders.cpp | @@-206, @@-219 | miss cache default ON (`LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT`, `0` = OFF build); one-time INFO line | 9567FE3F → 4B8250E9 |
| rexglue-sdk (gitlink) | — | 5350b1d → the new SDK HEAD after §4's 2 SDK commits | — |

- `shaders.cpp` is a native-fingerprint input: 9b40acbbef4c57b3 → 1616ce65e973c583.
- Do not stage `thirdparty/plume` in the superproject, or `thirdparty/fmt` / `thirdparty/simde` in the SDK. Stage by explicit path only; no `git add -A` / `commit -a`.

## 2. `git apply --check` against the live trees (no apply)

The commands were run at 15:49. Every result is exit 0, with core.autocrlf both `false` (the form the diff was made for) and `true` (the repos' setting). `-v` printed "Checking patch …" for every file and nothing else.

| cwd | command | result |
|---|---|---|
| rexglue-sdk | `git -c core.autocrlf=false apply --check -v final-sdk.diff` | exit 0 (9 files) |
| rexglue-sdk | `git -c core.autocrlf=false apply --check -v s33-popin-no5.patch` (4061ED2D) | exit 0 (4 files) |
| rexglue-sdk | `git -c core.autocrlf=false apply --check final-sdk.diff s33-popin-no5.patch` | exit 0 |
| rexglue-sdk | the same 3 with core.autocrlf=true | exit 0 |
| DimensionsRecomp | `git -c core.autocrlf=false apply --check -v final-super.diff` | exit 0 (2 files) |
| DimensionsRecomp | the same with core.autocrlf=true | exit 0 |
| DimensionsRecomp | `git -c core.autocrlf=false apply --check -p2 --include='rexlego/*' build\agent2\final\FINAL-DEFAULTS.diff` (unsplit form) | exit 0 |

The 57CFA8AD patch (nohunk5) was checked by a real apply in a scratch copy of the 4 live files (§3, `combo-check.py`): exit 0, alone and together with final-sdk.

## 3. Do they apply together, and is the combined source what was built?

**Together: yes.**
- The FINAL SDK files (9) and the #33 files (4) are disjoint.
- `git apply --check final-sdk.diff <s33>` exits 0 on live 5350b1d, for both s33 variants.
- In the scratch tree, with live copies, the combined apply exits 0.

**Base equality:**
- `snap1` (what every tonight bin was built from) == live, file by file over `git ls-files` (thirdparty/ skipped; `cmp-snap1.py`):
  - **rexglue-sdk:** 1287/1287 identical.
  - **superproject:** all 766 files snap1 has are identical (all of `rexlego/` 284, `tools/` 474, root 9), except `.gitignore`. c9e215f adds `!/perf/` there; it is not a build input.
  - The 4690 superproject files snap1 lacks are `perf/`, installers, docs, `.github`, `xexdump`, `DimensionsModManager-CLI`. None are game build inputs.

**Per-file results (`combo-check.py`, live copies + patches, sha256 compared):**

| applied to live | result |
|---|---|
| FINAL (sdk + super) alone | 11/11 files == devfinal/nativefinal overlay sources (`final/work/new` = prep-final after-hashes) |
| 57CFA8AD alone | 4/4 == devoff4b-s33-bin MANIFEST after-hashes |
| 4061ED2D alone | 3/4. `pipeline_cache.h` CB5BDBB9 ≠ 0BAF28BE (the missing comment) |
| FINAL + 57CFA8AD | 9 FINAL files == devfinal source, 4 #33 files == devoff4b-s33 source, 0 mismatches |

**Gaps: the combined source has never been built or timed as one binary.**
1. **devfinal / devfinal-off were built without #33.** Their rexgpu-xenos.dll (CB3A2CC9) has FINAL's shared_memory.cpp but the old d3d12 files. A build of the committed tree gives a rexgpu-xenos.dll different from both CB3A2CC9 and devoff4b-s33's DLL.
2. **devoff4b-s33 was built without FINAL.** It used devoff4b's exe and rexruntime.dll (the old defaults), with only rexgpu-xenos.dll rebuilt. The #33 rows timed #33 on the s0 defaults, not on win3.
3. **#33 "default OFF" does not leave the binary's behaviour untouched.** With the cvar at false:
   - the slow-frame report line gains 2 fields: `dropped draws {}` and `forced pipeline waits {:.1f} ({}x)`;
   - IssueDraw now counts `kDroppedDraw` on the existing async skip path;
   - EndSubmission's wait is moved into `AwaitPipelineCreation()` with the same logic.

   No log needle or expect that parses the slow-frame line was checked here.
4. **nativefinal is N-A: the new native exe + native4b's old snap1-sdk DLLs** (rexruntime A33801D1, rexgpu E3CB99CF). So no native bin has run with the win3 SDK defaults. A native build from the committed tree would link the new SDK: win3 rexruntime defaults, and #33 code in rexgpu. That combination is untimed.
5. **No exe build in the committed form.** devfinal's exe and the native exe were relinked from the snap1-off/on builds with only the changed TUs recompiled. A clean build of the committed tree is the first full build of this source.

**Recommendation:** after the commits, do one clean build of the committed tree (Xenos + native) and run M8's smoke run + `check-defaults.py --mode xenos` (and `--mode native` for the native bin, since its SDK DLLs are now new) before calling it a release. M10 to rate.

## 4. Proposed commits (SDK first, then the superproject gitlink)

Line endings: the patches are LF, and so are the files' working-tree bytes (the prep MANIFESTs show CRLF 0). Apply with `git -c core.autocrlf=false apply`.

Before each commit, run:
- `git diff --check`
- `git diff --stat` (must list exactly the files below)
- the after-hash check: the after column of §1 must match; `combo-check.py` does this on a scratch copy.

### SDK commit 1 (rexglue-sdk, perf/opt, parent 5350b1d)

```
cd DimensionsRecomp\rexglue-sdk
git -c core.autocrlf=false apply --check <WS>\build\agent2\session3\commit-plan\final-sdk.diff
git -c core.autocrlf=false apply <WS>\build\agent2\session3\commit-plan\final-sdk.diff
git add -- src/core/clock.cpp src/core/timer_queue.cpp src/graphics/shared_memory.cpp src/kernel/xboxkrnl/xboxkrnl_rtl.cpp src/kernel/xboxkrnl/xboxkrnl_threading.cpp src/system/runtime.cpp src/system/xmemory.cpp src/system/xobject.cpp src/system/xthread.cpp
```

Message:
```
S4 final defaults: ship the win3 timer and physical-protect defaults

Flip 12 cvar defaults to the configuration confirmed in the S4 window C
"win3" arm:
- p2fc: shared_memory_single_hold_rearm (P2), physical_protect_hold_global_lock
  (fix (i)) and physical_protect_keep_watch (C1 v3) default on;
  physical_protect_keep_watch_verify stays off.
- d11p: host_timer_resolution_ms=1, host_timer_throttling_optout,
  precise_guest_sleep, wait_timeout_round_up, cs_spin, spinlock_pause_spin,
  clock_lockfree, tls_bounds_fix and timer_queue_precise_wait default on.

Log the effective values once at startup, with where each came from
(default/config/env/cmdline/runtime): "Final defaults:" in Runtime::Setup and
"Final defaults (GPU):" in SharedMemory::InitializeCommon. A plain launch
shows every key as (default).

All 12 stay settable; the old behaviour is these cvars at their previous values
(see the release notes). CG26 is not part of this change.
```

### SDK commit 2 (rexglue-sdk, parent = commit 1)

```
git -c core.autocrlf=false apply --check <WS>\build\agent6\s33-popin\s33-popin-nohunk5.patch
git -c core.autocrlf=false apply <WS>\build\agent6\s33-popin\s33-popin-nohunk5.patch
git add -- include/rex/graphics/d3d12/pipeline_cache.h src/graphics/d3d12/command_processor.cpp src/graphics/d3d12/pipeline_cache.cpp src/graphics/frame_stats.h
```

Message:
```
d3d12: add d3d12_pipeline_creation_no_wait (opt-in, default off) (#33)

With async_shader_compilation, a draw whose pipeline is still being created is
skipped and EndSubmission waits for every pipeline in creation, which can
stall. With d3d12_pipeline_creation_no_wait=true, EndSubmission no longer waits:
such draws stay skipped until their pipeline is ready, trading a stall for a
few frames of pop-in. Draws that memexport or run inside an occlusion query
still wait for their pipeline (the guest reads their results).

The mode is latched in PipelineCache::Initialize and only takes effect with
async_shader_compilation, pipeline creation threads and bindless resources;
otherwise it is ignored with a warning. Requires restart. Shutdown of the
shader storage waits for in-flight creation in this mode.

Also, regardless of the cvar: EndSubmission's wait moves into
AwaitPipelineCreation() (same logic), and the slow-frame report gains
"dropped draws" and "forced pipeline waits" (new frame_stats ids kDroppedDraw,
kPipelineAwait).

Default off: suggested opt-in for users who prefer pop-in over shader stalls.
```

### Superproject commit (DimensionsRecomp, perf/opt, parent c9e215f)

```
cd DimensionsRecomp
git -c core.autocrlf=false apply --check <WS>\build\agent2\session3\commit-plan\final-super.diff
git -c core.autocrlf=false apply <WS>\build\agent2\session3\commit-plan\final-super.diff
git add -- rexlego/src/gpu_wait_backoff.cpp rexlego/src/gpu_native/shaders.cpp rexglue-sdk
git diff --cached --submodule=short   # gitlink 5350b1d -> <SDK commit 2>; nothing from thirdparty/
```

Message (matches the repo's "…; SDK at S4b" style):
```
S4 final defaults: GPU wait back-off 500 us, native shader miss cache on; SDK at S4 final

- GPU wait back-off (Xenos only) is on by default at Q=500 us, spin 30 us
  (S4 window C "win3"). LEGO_GPU_WAIT_BACKOFF_US: unset/empty = the build
  default, "off" = off, digits = Q in us, anything else = warning + off.
  Builds can set -DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1 for an off default.
  Before Windows 10 1803 the back-off falls back to SwitchToThread.
- Native shader miss cache is on by default (W8a: -28.6 % median).
  LEGO_NATIVE_SHADER_MISS_CACHE=0 turns it off; LEGO_DUMP_MISSING_SHADERS
  still turns it off. -DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0 for an off
  build. shaders.cpp is a fingerprint input: native GPU fingerprint
  9b40acbbef4c57b3 -> 1616ce65e973c583, so saved pipeline recipes and
  precompiled packs for the old fingerprint are rebuilt (one cold launch).
- rexglue-sdk 5350b1d -> <new>: win3 cvar defaults + "Final defaults" log
  lines; d3d12_pipeline_creation_no_wait opt-in (default off, #33).
```

## 5. Part B: one final bin pair from the committed source (`build/agent2/final2/`)

**Starts only after the Overseer's "pushed <sha>".** Before any heavy step, `bench\agent5\day\status\state.txt` must say `waiting-for-go` (15:53: yes, launcher pid 24624, deadline 20:00) and no `legodimensions.exe` may be running (`Get-Process legodimensions -EA 0` is empty). `perf-notes\WINDOW-HOLD.txt` is respected as in final/.

**Method: incremental, the same as final/, with the same tools copied to `final2/`.** Base trees: snap1 (== live 5350b1d/c9e215f, §3), snap1-sdk/snap1-off/snap1-on build dirs for objects and the PCH, used read-only. Overlay sources = **the committed blobs** (`git show <sha>:<path>`, read-only), not the patch files, so the bins are built from exactly what was pushed.

Bins:
- `devfinal2-bin` = devoff4b-bin + rexruntime.dll (rt) + rexgpu-xenos.dll (gpu, FINAL + #33) + legodimensions.exe/.map (xe).
- `nativefinal2-bin` = native4b-bin + rexruntime.dll (rt) + rexgpu-xenos.dll (gpu) + legodimensions.exe/.map (nat). **Not N-A:** the committed native build links the new SDK, so the new DLLs are staged too. This closes gap 4.
- No OFF bins (not asked).

### What changes in the final2 tool copies (vs final/, rated 94CC9FA7)

| tool | change |
|---|---|
| `prep-final2.py` (from prep-final.py) | Paths `final` → `final2`. Overlay source = committed blobs of the 13 SDK + 2 superproject files; before-hash = snap1, after-hash = committed blob = §1 "after" column (must match, or STOP). Adds the 4 #33 files: `src/graphics/d3d12/{command_processor,pipeline_cache}.cpp`, `src/graphics/frame_stats.h`, and `include/rex/graphics/d3d12/pipeline_cache.h` via an overlay include dir with `--include-first` (the devoff4b-s33 method, `session3/prep-s33.py`). |
| `fsyntax2.py` | gpu set 1 → 10 TUs (shared_memory.cpp + the 9 d3d12 TUs below). Count gate 8/10/1/4 = 23 (rt/gpu/xe/nat; no OFF legs). |
| `build-final2.py` | gpu leg = 10 TUs (ninja deps of `pipeline_cache.h`/`frame_stats.h` in rexgpu-xenos, as built for devoff4b-s33): `shared_memory.cpp`, `command_processor.cpp`, `d3d12/{command_processor,deferred_command_list,graphics_system,pipeline_cache,primitive_processor,render_target_cache,shared_memory,texture_cache}.cpp`. Stages `devfinal2`, `nativefinal2` (with rt + gpu). `OVERLAY_RE` → `agent2/final2/b/`. Adds the gpu needle `d3d12_pipeline_creation_no_wait`. |
| `check-defaults.py`, `pe-check.py`, `pe-diff.py`, `verify-bins.py`, `recompile.py`, `relink.py`, `stage-variant.py` | Unchanged, used by path. `check-defaults --mode native` (new SDK DLLs), not native-old. |

> [!IMPORTANT]
> Rating B2 applies: a header (`pipeline_cache.h`) is in the diff, so PCH reuse needs M10's rating. The precedent is devoff4b-s33 (the same header, the same `--include-first` overlay, the PCH reused, gpu CTL == E3CB99CF except the TDS; `r33-nohunk5-diagd.md`). I'll send M10 the 3 tool diffs vs final/ before the push, so the rating isn't on the critical path.

### Exact commands (WS root)

```
# step 0: verify the push (read-only)
git -C DimensionsRecomp\rexglue-sdk diff --stat 5350b1d <sdk-sha>      # exactly the 13 files of §1
git -C DimensionsRecomp diff --stat c9e215f <super-sha>                # exactly 2 files + rexglue-sdk gitlink
git -C DimensionsRecomp ls-tree <super-sha> rexglue-sdk                # gitlink == <sdk-sha>
python build\agent2\final2\prep-final2.py --dry-run --sdk <sdk-sha> --super <super-sha>   # committed blob hashes == §1 after column, else STOP
python build\agent2\session3\commit-plan\cmp-snap1.py                  # all other files still == snap1
Get-Content bench\agent5\day\status\state.txt                          # waiting-for-go; no legodimensions.exe running

# step 1: overlay + fsyntax
python build\agent2\final2\prep-final2.py --sdk <sdk-sha> --super <super-sha>
python build\agent2\final2\fsyntax2.py                                 # 23 TUs, all exit 0

# steps 2-4: legs, in order rt -> gpu -> xe -> nat (each: CTL leg first, STOP on any gate failure)
python build\agent2\final2\build-final2.py --leg rt   --jobs 8   # CTL == devoff4b rexruntime except the TDS; needle "Final defaults:{}"
python build\agent2\final2\build-final2.py --leg gpu  --jobs 8   # CTL == E3CB99CF except the TDS; needles "Final defaults (GPU): {} {}", "d3d12_pipeline_creation_no_wait"
python build\agent2\final2\build-final2.py --leg xe   --jobs 8   # CTL == devoff4b exe + map; needle "GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US="
python build\agent2\final2\build-final2.py --leg nat  --jobs 8   # CTL == native4b exe + map; miss-cache needle, 1616ce65e973c583 present, 9b40acbbef4c57b3 absent

# step 5: stage + verify (writes only the 2 new bin dirs)
python build\agent2\final2\build-final2.py --stage devfinal2
python build\agent2\final2\build-final2.py --stage nativefinal2
python build\agent2\session3\verify-bins.py build\agent2\devfinal2-bin build\agent2\nativefinal2-bin build\agent2\devoff4b-bin build\agent2\devoff4b-cg26-bin build\agent2\native4b-bin
python build\agent2\final\pe-check.py <each new DLL/exe>          # exports/imports vs the reference
# + D6: re-verify the 3 shared-bin MANIFESTs; write final2\BIN-PINS.md (every file sha256, MANIFEST sha, tool shas)
```

**Default gates (static, before any run):**
- ON: rt needle `Final defaults:{}`, gpu needle `Final defaults (GPU): {} {}`, xe back-off needle (the OFF string is only the env-off branch; the q500 default is proven by the source line `#define LEGO_GPU_WAIT_BACKOFF_DEFAULT_US 500` in the committed blob and at runtime by check-defaults), nat miss-cache needle + fingerprint 1616ce65e973c583.
- OFF: the committed `pipeline_cache.cpp` blob has `REXCVAR_DEFINE_BOOL(d3d12_pipeline_creation_no_wait, false`; the gpu DLL contains the cvar name (code present).

### Smoke (short)

Per bin, a plain launch (cvars: `framerate_limit=0` only, no `LEGO_*` env) to first 3D, then close:
- `bench\agent8\run\first-boot.ps1 -BinDir build\agent2\<bin> -Tag <bin>-smoke -WatchSeconds 120`
- `python build\agent2\final\check-defaults.py <game.log> --mode xenos` (devfinal2) / `--mode native` (nativefinal2): every key (default), the full back-off line incl. `; stats OFF; GetData hook built.` (xenos), miss cache ON (native).
- The game.log has neither `d3d12_pipeline_creation_no_wait: not waiting` (INFO) nor `… ignored` (WARN): proves the default OFF at runtime.
- No WER, no dialogs, clean exit.

> [!NOTE]
> `first-boot.ps1` writes to `build/agent8/runs/`, which is outside my write scope. Either M8 runs these 2 boots, or the Overseer allows me to run first-boot.ps1.

### ETA

| step | time |
|---|---|
| final2 tool copies + diffs to M10 (read/write only, can run **before** the push) | ~30 min |
| step 0 verify | ~3 min |
| prep + fsyntax | ~3 min |
| 4 legs (rt 8 TUs, gpu 10 TUs, xe 1, nat 4, each with its CTL) | ~6-8 min |
| stage + verify-bins + pe-check + BIN-PINS | ~5 min |
| smoke (2 boots + checks) | ~10-15 min |

**~30 min from "pushed <sha>" to the smoke result**, if the tools are rated before the push (otherwise add the rating time). That fits the 17:30-18:00 slot.

**Alternative (not proposed):** a clean configure + full build of the committed tree in a fresh copy (never `cmake --install`). It removes the incremental-relink caveat (gap 5) but takes about 30-90 min, and its bins would not be CTL-comparable to the timed ones.

## Files in this folder

| file | purpose |
|---|---|
| `split-final.py` | splits FINAL-DEFAULTS.diff into `final-sdk.diff` + `final-super.diff` and checks the split |
| `final-sdk.diff`, `final-super.diff` | per-repo patches (sha256 above) |
| `cmp-snap1.py` | snap1 vs live, file by file (read-only) |
| `combo-check.py` | scratch apply of live copies in `work/` (outside any repo) + hash compare vs the bins' sources |
| `work/` | scratch trees from combo-check: final-sdk, final-super, s33-no5, s33-nohunk5, combo-no5, combo-nohunk5 |
