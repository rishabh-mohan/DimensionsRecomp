# FINAL defaults table (M2, 2026-11-25)

The change set is `build/agent2/final/FINAL-DEFAULTS.diff`. It applies with `git -c core.autocrlf=false apply` from the WS root, to the live tree (`--check` only) or to the snap1 tree. Paths are `DimensionsRecomp/...`. The 11 before-files are byte-identical in live HEAD (game c9e215f, SDK 5350b1d) and in `build/agent2/snap1`.

**Ship = WC "win3", exactly as timed.** Source: `bench/agent8/run/matrix-windowC.json` (00E3EE97), arm `win3` on `build/agent2/devoff4b-bin`. Confirmed by `build/agent10/session3/readout-night-xcheck.md`.

win3 = three groups, as the arm's note says:
- **p2fc**: P2, fix (i), C1 v3, verify off.
- **d11p**: the 8 timer cvars plus `timer_queue_precise_wait`.
- **q500**: back-off 500 us, spin 30 us.

**CG26 stays off. P2 stays in** (xcheck S3 option (a)).

File:line points to the default in the **after** tree. Old line numbers are the same for every SDK cvar.

## SDK cvars (rexglue-sdk; code default in the `REXCVAR_DEFINE_*` line)

| key | old | new | win3 value | source arm | default at (after) | DLL |
|---|---|---|---|---|---|---|
| `shared_memory_single_hold_rearm` (P2) | false | **true** | true | win3 / p2fc | `src/graphics/shared_memory.cpp:34` | rexgpu-xenos |
| `physical_protect_hold_global_lock` (fix (i)) | false | **true** | true | win3 / p2fc | `src/system/xmemory.cpp:46` | rexruntime |
| `physical_protect_keep_watch` (C1 v3) | false | **true** | true | win3 / p2fc | `src/system/xmemory.cpp:55` | rexruntime |
| `physical_protect_keep_watch_verify` | false | false (unchanged) | false | win3 / p2fc | `src/graphics/shared_memory.cpp:43` | rexgpu-xenos |
| `host_timer_resolution_ms` (UINT32) | 0 | **1** | 1 | win3 / d11p | `src/system/runtime.cpp:39` | rexruntime |
| `host_timer_throttling_optout` | false | **true** | true | win3 / d11p | `src/system/runtime.cpp:42` | rexruntime |
| `precise_guest_sleep` | false | **true** | true | win3 / d11p | `src/system/xthread.cpp:55` | rexruntime |
| `wait_timeout_round_up` | false | **true** | true | win3 / d11p | `src/system/xobject.cpp:35` | rexruntime |
| `cs_spin` | false | **true** | true | win3 / d11p | `src/kernel/xboxkrnl/xboxkrnl_rtl.cpp:51` (macro at :50) | rexruntime |
| `spinlock_pause_spin` | false | **true** | true | win3 / d11p | `src/kernel/xboxkrnl/xboxkrnl_threading.cpp:49` (macro at :48) | rexruntime |
| `clock_lockfree` | false | **true** | true | win3 / d11p | `src/core/clock.cpp:26` | rexruntime (rexcore OBJECT lib) |
| `tls_bounds_fix` | false | **true** | true | win3 / d11p | `src/system/xthread.cpp:59` | rexruntime |
| `timer_queue_precise_wait` | false | **true** | true | win3 / d11p | `src/core/timer_queue.cpp:31` | rexruntime (rexcore OBJECT lib) |
| `framerate_limit` | (unchanged) | (unchanged) | 0 | bench setting of every WC arm | not changed | - |

- `framerate_limit=0` is the bench's uncapped setting, used by every arm including s0. It is **not** a shipped default.
- The comments that said "default off" right above 5 of these cvars now say "default on". These are at `timer_queue.cpp:29`, `shared_memory.cpp:27`, `runtime.cpp:38`, `xmemory.cpp:45` and `xmemory.cpp:50`. Line counts are unchanged.

## Environment keys (game side)

| key | old default (unset/empty) | new default (unset/empty) | win3 value | source arm | default at (after) | builds |
|---|---|---|---|---|---|---|
| `LEGO_GPU_WAIT_BACKOFF_US` | OFF | **ON, Q 500 us** (`LEGO_GPU_WAIT_BACKOFF_DEFAULT_US`) | 500 | win3 / q500 (W9) | `rexlego/src/gpu_wait_backoff.cpp:80` (`#define ... 500`), used at :102 and :146 | Xenos only (N3) |
| `LEGO_GPU_WAIT_SPIN_US` | 30 | 30 (unchanged) | 30 | win3 / q500 | `rexlego/src/gpu_wait_backoff.cpp:116` (`uint32_t spin_us = 30`) | Xenos only |
| `LEGO_NATIVE_SHADER_MISS_CACHE` | OFF | **ON** (`LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT`) | n/a: native-only | W8a `mc` (native4b, -28.6 % median) | `rexlego/src/gpu_native/shaders.cpp:225` (`#define ... 1`), used at :234 | native only |

**q500.** The `gpu_wait_backoff.cpp` hunks are M9's `build/agent9/session3/q500/q500-default.diff` (28F0D1DE), verbatim: `verify-diff.py` checks the section byte for byte. The file goes 01D9F8F3 → 74115EEA. Values:
- unset or empty: the build default (500);
- `off` (any case, exact): OFF, with one INFO line;
- digits: Q as before;
- anything else: WARN, back-off OFF.
- **Release notes (q500 rating S2):** `LEGO_GPU_WAIT_BACKOFF_US=off` is the user's off switch. Before Win10 1803 the back-off falls back to SwitchToThread.

**Miss cache.** Values:
- unset or empty: the build default (1 = ON);
- `0`: OFF;
- any other value: ON, as before;
- `LEGO_DUMP_MISSING_SHADERS` set: OFF, as before (capture runs keep the full path).

What the miss cache touches:
- **Code:** only `ShaderMissCacheEnabled()` in `shaders.cpp`, plus its comment. This TU is in the native GPU build only (CMakeLists L61-141).
- **Native fingerprint:** `shaders.cpp` is a fingerprint input (CMakeLists L735). The native fingerprint changes from `9b40acbbef4c57b3` to `1616ce65e973c583` (predicted by `predict-fingerprint.py`; it reproduces the pinned value from the current 271 inputs first).
  - The generated `native_gpu_build_info.h` changes, so `device.cpp`, `shader_archive.cpp` and `pipeline_library.cpp` (via `pipeline_recipes.h`) recompile.
  - Saved startup pipeline recipes and any additive precompiled pack built for the old fingerprint are rejected ("pack build or compiler provenance mismatch"). The first launch of the new native exe is a cold one.
  - This is the miss cache's re-pin, not q500's. q500's rating condition "native fingerprint unchanged" still holds for q500 alone.
- **Log:** a new one-time INFO line, `Native GPU: shader miss cache ON (build default)`. It reads `... (LEGO_NATIVE_SHADER_MISS_CACHE set)` when the env var is set, and adds a note when the capture env var turns the cache off.

## Proof lines added (for `check-defaults.py`)

| line | where | builds |
|---|---|---|
| `Final defaults: <11 rexruntime keys as name=value(source)>` | `rexglue-sdk/src/system/runtime.cpp:77`, called at :171 in `Runtime::Setup` right after host timing (not in tool mode) | every bin on the new SDK |
| `Final defaults (GPU): shared_memory_single_hold_rearm=..(..) physical_protect_keep_watch_verify=..(..)` | `rexglue-sdk/src/graphics/shared_memory.cpp:80`, end of `SharedMemory::InitializeCommon` | bins that create the Xenos SharedMemory |
| `Native GPU: shader miss cache ...` | `rexlego/src/gpu_native/shaders.cpp`, first call of `ShaderMissCacheEnabled()` | native |

- The source is one of `default`, `config`, `env`, `cmdline` or `runtime` (`rex::cvar::Source`). It comes from `GetFlagSource`. A name that is not registered prints `=unregistered`.
- A plain launch must show every key `(default)`.
- **What the log cannot prove.** The q500 ON line for env unset is identical to env 500 (q500 rating R3). Whether `LEGO_GPU_WAIT_BACKOFF_US` was really unset comes only from run.json `env_set` and the bin id.

## Scope of the claim (xcheck S2)

The WC result covers:
- one light route (~226 draws/frame);
- uncapped (~450-490 fps);
- AC power;
- this thermally limited laptop.

The idle and battery cost of `host_timer_resolution_ms=1` + `host_timer_throttling_optout=true` was not measured. At a 60 fps cap, the benefit is CPU headroom and tail, not fps. The "~1 core less" is the most transferable number.

## OFF semantics on new bins

- **SDK cvars:** no build define. An OFF/ref arm on a new bin sets the old values explicitly. All 12 changed cvars are settable at launch; the 3 init-only ones (hold_global_lock, keep_watch, timer_queue_precise_wait) are settable on the command line or in config.
  - The OFF set: `shared_memory_single_hold_rearm=false physical_protect_hold_global_lock=false physical_protect_keep_watch=false host_timer_resolution_ms=0 host_timer_throttling_optout=false precise_guest_sleep=false wait_timeout_round_up=false cs_spin=false spinlock_pause_spin=false clock_lockfree=false tls_bounds_fix=false timer_queue_precise_wait=false`
- **Back-off:** `LEGO_GPU_WAIT_BACKOFF_US=off` (lowercase, q500 rating N1). An OFF bin instead builds with `-DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1`, recorded in its MANIFEST.
- **Miss cache:** `LEGO_NATIVE_SHADER_MISS_CACHE=0`. A native OFF bin instead builds with `-DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0`, recorded in its MANIFEST.
- **Exact old behaviour:** the existing bins (devoff4b-bin, native4b-bin, on `snap1-sdk`) remain the s0/n0 references.
