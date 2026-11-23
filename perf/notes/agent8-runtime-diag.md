# Agent 8 / task 7: always-on runtime overhead of diagnostics and background threads (analysis only)

Status: this is analysis only, because of the STOP ORDER (no toolchain, no builds). **I made no source edits**,
so the repository is untouched by me. Paths are relative to `DimensionsRecomp/`.

## Ranked findings

### 1. `native_scene_diagnostics` is ON by default, so every guest heap alloc and free pays for journaling (Native GPU build)
- **Where:** `rexlego/src/native_skin_diagnostics.cpp:14-16` (`REXCVAR_DEFINE_BOOL(native_scene_diagnostics, true, ...)`,
  "in this diagnostic development build", kInitOnly). The file only compiles under `LEGODIMENSIONS_NATIVE_GPU`, which is
  the 0.2.0 shipping path.
- **What is slow:** with the default value of `true`:
  - Every free (`sub_82A34208`, `:171-196`) saves and restores a 28-byte TLS struct, then runs **two**
    `heap_journal.Record()` calls.
  - Every allocation (`sub_82A33D28`, `:205-212`) runs one `Record()`.
  - `Record()` (`native_heap_journal.h:49-59`) hashes the pointer, takes a **bucket spinlock** (`atomic_flag`
    test_and_set loop, `:27-33`), then runs `sequence_.fetch_add` on **one global atomic shared by every guest
    thread** (`:55`). That is a `lock xadd` on a contended cache line for each guest malloc/free, and it serialises the
    allocator-heavy threads.
  - `sub_82C9A000` (`:158-169`) logs 1 + 7 + up to 8 lines per NuCpuSkin teardown. `HexWords` (`:40-44`) builds each
    line with `std::ostringstream`, so level unloads pay for thousands of ostringstream-formatted log lines.
  - `sub_82E0F480` and `sub_82DD3220` copy 16 to 34 guest words through `CopyNativeGuestMetadata` per tree cleanup
    call.
- **Proposed change (ranked):**
  - (a) Product decision: default the cvar to `false` in release builds, keeping `true` for dev builds or via toml. The
    off path is then one bool test per alloc/free, which is the existing code at `:182` and `:207`. This changes what a
    crash log contains, so it needs owner sign-off.
  - (b) Behaviour-preserving even when ON: replace the `ostringstream` in `HexWords` with a fixed hex writer
    (`fmt::format_to` into a `fmt::memory_buffer`, `{:08x}` joined by commas). The output is byte-identical. Verify
    with a randomised old-vs-new string-equality test.
  - (c) Put `alignas(64)` on `Journal::sequence_` so it does not false-share with bucket 8191. This is minor.
  - The global sequence counter itself cannot go without changing the meaning of `seq=` in the logs.
- **Risk:** (a) loses the heap-history lines from crash logs by default. (b) and (c) carry no behaviour risk.
- **Verify once a build exists:**
  - Microbenchmark: `Journal::Record` with 1, 2, 4 and 8 threads, ns/op.
  - In game: ETW or sample-profiler time in `sub_82A33D28` / `sub_82A34208` with the cvar on and off, and the length
    of the level-unload hitch.

### 2. The Discord presence thread wakes 10×/s even when nothing changes
- **Where:** `rexlego/src/discord_presence.cpp:387-391` (20 × `sleep_for(100ms)` per 2 s tick). `discord_rpc`
  defaults to **true** (`:46`), so this thread runs for every player.
- **What is slow:** 10 wake-ups per second, forever. When Discord is not running, every 2 s brings 10 × `fmt::format`
  plus 10 failing `CreateFileA` calls (`:174-185`). When connected, each tick calls `CurrentDetails()`, which copies a
  cvar string (`:372`). The cost is small, but it is pure background noise on a 12-thread laptop CPU.
- **Proposed change:** `std::mutex` + `std::condition_variable g_wake`. Replace the slice loop with
  `std::unique_lock l(m); g_wake.wait_for(l, 2s, []{ return !g_running.load(); });` and have `Stop()` call
  `g_wake.notify_all()` after the exchange.
  - The cadence (2 s) stays the same. Wake-ups drop from 10/s to 0.5/s, and Stop latency drops from up to 100 ms to
    immediate.
  - Optionally build the 10 pipe names once (static array) instead of `fmt::format` on every retry.
- **Risk:** low. Shutdown ordering is unchanged, since `join` still follows.
- **Verify:** a standalone test that runs the thread-loop skeleton old and new, counting wake-ups per 10 s and
  measuring Stop() latency (median of 5 runs).

### 3. The first Toy Pad placement is slow: the cause is not in `toypad_app.cpp`
- `rexlego/src/toypad_app.cpp` only resolves the path and launches LegoToypad.exe once (at startup or from a button).
  It has no polling and no socket, so nothing there runs per placement.
- The portal listener lives in the SDK: `rexglue-sdk/src/input/portal/emulated_toypad.cpp`.
  - It has a blocking `accept` (`:995`) with no lazy init on the first event, and a thread per client (`:1013`).
  - LOAD and REMOVE hang up immediately (`:963-965`, the comment at `:850-855` says why).
  - Only MOVE sleeps on purpose (`kMovePickupDelay`, `:952`).
  - Socket handling is therefore unlikely to explain a *first-per-run* slowdown.
- **Ranked hypotheses, all need the game:**
  1. First-use asset streaming of the character and vehicle model, plus Native GPU first-use shader/pipeline
     compilation. Both match "per run, characters and vehicles".
  2. `LoadFigure` reading the tag file through `path`, a cold file cache on first access.
- **Verify:** compare the timestamp of the log line `Toypad listener: LOAD -> pad=` with the first frame in which the
  figure appears, then add the pipeline-compile logs from the same window.
- **Also always-on, in the SDK and outside my files:** `PickerWatchRun` (`emulated_toypad.cpp:1034-1056`) polls every
  50 ms (20 wake-ups/s) and re-runs `OpenEventW` every 1 s for the whole session. It could wait on the event with a
  timeout instead. That needs the SDK owner.

### 4. `name_trace.cpp`: the off path costs a cvar accessor call plus a `std::string` construct and destroy per path hash
- **Where:** `rexlego/src/name_trace.cpp:31-49`. `sub_82A3D980` is TT's path hash, called for every archive name
  lookup, so the volume is high during loads.
- **What is slow:** when the filter is empty, each call still runs `REXCVAR_GET` and constructs and destroys
  `std::string name` (SSO, no heap allocation). `REXCVAR_GET` is a call to `FLAGS_x_storage_()` (`cvar.h:343`,
  `:357`), possibly a function-local static.
- **Proposed change:** add `if (filter.empty()) { __imp__sub_82A3D980(ctx, base); return; }` before declaring `name`.
  The output is identical.
- **Risk:** none.
- **Gain:** a few ns per lookup, during loads only. Low priority.
- The other hooks in the file (`:72-137`) test only bools; they are fine.

### 5. `tt_lock_trace*`: not in a default build
- `CMakeLists.txt:143-154` adds `tt_lock_trace.cpp` only under `LEGODIMENSIONS_TT_LOCK_TRACE`, which defaults to OFF.
  The draw-scope define likewise only applies when that option is on. Default cost is zero.
- When the option is built but the env var is unset, every `NativeDrawScope` and `RenderScope` calls `Enabled()`. That
  runs a guarded function-local static plus a try block (`tt_lock_trace.cpp:24-26`, `:85`).
- **Proposed change:** cache it once as a namespace-scope `const bool kEnabled` computed from the env var at static
  init.
- **Risk:** low; this is a diagnostic build only.

### 6. `sample_profiler.cpp`: off path is zero; on path is inaccurate
- When off: one `getenv` at static init (`:154-159`), no thread, no runtime cost.
- When on:
  - `timeBeginPeriod(1)` (`:100`) holds 1 ms timer resolution for the whole process even while idle. That is an
    observer effect.
  - While recording, `CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD)` (`:125`) snapshots **all threads in the system**
    on every sample, and each thread is opened and closed every time (`:130-145`). The real sample rate is likely far
    below the "~1 ms" the comment claims.
- **Proposed change (diagnostic quality, not game speed):**
  - Call `timeBeginPeriod` and `timeEndPeriod` only around recording.
  - Cache the thread list and handles, refreshing every ~100 ms.

### 7. `crash_guards.cpp`: no vectored handler here; already minimal
- The file has no VEH. It contains:
  - two hooks, each with one compare per loop iteration (`:109`, `:307`); the atomic and the log run only on the
    null path;
  - two one-compare mid-asm helpers (`:55-64`).
- The only `AddVectoredExceptionHandler` call is in the SDK at `rexglue-sdk/src/core/exception_handler_win.cpp:305`. I
  did not have time to audit its first-test ordering. That belongs to the SDK owner.
- `crash_popup.cpp` runs once at static init (one `CommandLineToArgvW`); its cost is negligible.

## Files I did not get to (or only skimmed)
- `rexglue-sdk/src/core/exception_handler_win.cpp`: the VEH fast-reject order; not read.
- `rexglue-sdk/src/input/portal/emulated_toypad.cpp`: I read only lines 840-1060 (`LoadFigure`/`RemoveFigure`
  internals and the guest-side event path were not read).
- `rexlego/src/gpu_native/guest_metadata.h` (`CopyNativeGuestMetadata` cost) and the `slot_growth.h`
  `AllocationAttemptScope` cost, both on the alloc path.
- No benchmarks or tests were written in `bench/agent8/diag`; there was no toolchain and builds were stopped.
