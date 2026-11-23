# S3.4 / task #12 (c): `LEGO_NATIVE_SHADER_MISS_CACHE` stopgap (default OFF), for Agent 10's S4 review

Agent 4, 2026-11-22 ~06:00. **Scratch only.** No live apply and no build tonight (Agent 1's decision).
`shaders.cpp` is not an Agent 4 file. If option 1a (the AOT pack for VS 0xAC449538 / PS 0xAC448F28, see
`aot-pack-proposal.md`) lands first, this stopgap is moot and only useful as a measurement.

## Artifacts (all in `build/agent4/s34/`)

| File | sha256 | Notes |
|---|---|---|
| `shaders.before.cpp` | `E87A2DEE43D38D8EBBEE8EFD663DE70A293F7826B5AC0231B8B8A08E6A7E916D` | Copy of the live file: 41,029 B, 913 CRLF lines |
| `shaders.cpp` | `9567FE3F3B63637D9595D6B74B72567E1CAEA2D1A071E872D12660DFB37E1EFA` | Patched: 51,261 B, 1,131 CRLF lines |
| `shaders-s34.patch` | `328BDAE19ABFC6C8CD980847F8AE533A0360589760A1D67EFE7C2F4762F518DF` | 14,441 B, +229/-11, 9 hunks |
| `make_patch_s34.py` | | Checks the live sha, the line count and exact anchors, then edits bottom-up |
| `run_compiles.ps1`, `compile_copy_shaders.ps1` | | The four full `-c` compiles (1 thread, BelowNormal priority) |
| `objcheck.py`, `objcheck-v2.txt`, `objcheck-v3.txt` | | By-name object comparison (see Tests) |
| `warn_diff.py`, `warn-diff.txt`, `compile-*.log`, `objdiff-*.txt` | | Warning-set diff; raw logs |

Scratch trees: `build/agent4/s34tree/…/gpu_native/shaders.cpp` is the patched file and
`build/agent4/s34base/…/shaders.cpp` is the control (live bytes). Line numbers below refer to the patched file.

## What the patch does

- **Default (unset, or set to `0`):** OFF. `ShaderMissCacheEnabled()` (:222) reads the environment once into a
  function-local static. It is also forced OFF whenever `LEGO_DUMP_MISSING_SHADERS` is set (:224). That is the same
  predicate (`value && length > 1`) that enables `CaptureMissingPlacementShader` (:151-156), so a capture run never
  skips a capture.
- **ON, replay (`AdoptShader` :488):** the replay check runs after the per-call header checks, which are unchanged:
  `ReadableGuestRange` :456, the type check :463, and the container pointer :482-486.
  - It looks up the key (stage, guest, container) (:276, :353).
  - On a valid entry it does the same `g_shader_warning_count.fetch_add` (<16), prints the same line (:369-370) and
    returns `nullptr`, which is the same result as the full-path miss.
  - A hit skips `ReadableGuestSpan` (:493) and `FindShaderByMicrocode` (:501).
- **ON, full-path miss:**
  1. `ArmShaderMiss` (:500) runs **before** the lookup. It takes the pack generation, the prefix and the span, then a
     `WatchCpuMemory` stamp over `[container, container + span)`.
  2. After the existing capture and log, `RememberShaderMiss` (:514) runs:
     - It re-checks the prefix (:319).
     - It copies the 4 logged words.
     - It inserts only if the stamp is **still clean** after the lookup and those reads (:331).
     - It emits the `shader_miss_cache_insert` probe event, capped at 64 (:345-349).
- **Validity** (`ShaderMissValid` :280): the pack generation is unchanged AND `CpuMemoryUnchanged(stamp)`. A replay
  that finds a stale entry erases it (only if it is still the same entry) and falls through to the full path
  (:363-367).
- **Header writes can't make an entry stale.** The header is re-read on every call and the container pointer is part
  of the key, so only the code span needs the stamp.

## Agent 10 §15.2 conditions (`perf-notes/agent10-batch2-review.md:677-691`) mapped to the patch

| # | Condition | Where / how |
|---|---|---|
| 1 | Key (stage, guest, container) plus pack generation | One map per stage (:272) with key `(guest<<32)\|container` (:276). `pack_generation` is stored (:252) and compared on every replay (:281). `ArmShaderMiss` arms only at generation 0 (:298-299), because pack microcode is outside the static span table. At gen 0 the lookup result comes from static tables only (shader_archive.cpp:125-132), and `FindPrecompiledByMicrocode` returns null (:303). |
| 2 | Stamp over every byte `FindShaderByMicrocode` can read; max ≤ 64 KiB | The lookup hashes 8 prefix bytes, then `microcodeSize` bytes for each index entry of the same stage and prefix that fits `readable_size` (shader_archive.cpp:350). The span is the exact per-(stage, prefix) maximum `microcodeSize` from the same static table, with a minimum of 16 (`ShaderMissSpan` :231-245). Global max: VS 1,900 B, PS 2,024 B (index 19,116 entries: VS 2,481, PS 16,635). The two shaders: VS 0xAC449538 bucket `DCD4AD8441398283` has span 408; PS 0xAC448F28 zero-prefix bucket `C77B3ABB6F87ACD9` (6,636 entries) has span 2,024. Both spans fall on one 4 KiB page (0xED23D000). |
| 3 | `readable_size` as an input | Insert requires `readable_size >= span` (:302), so no candidate was skipped. More readable bytes later can't add candidates. Decommit/Release fire the watch callbacks (SDK xmemory.cpp:2098/2122), so the stamp goes dirty. The protect-only residual is listed below. |
| 4 | No stamp, no cache | `WatchCpuMemory` returns `{}` when the watch is off (memory_watch.cpp:101) or any span is non-physical (:109). `armed()` is then false (:266), so nothing is remembered (:514). `CpuMemoryUnchanged` is false on empty pages (:132). |
| 5 | Logs | The replay returns before :493, with the same counter (<16) and the same line through the shared `LogMissingPlacementShader` (:284-292). The full path uses the same helper (:506-513), with the same conditional word reads (`readable >= 12/16`, else 0) and the same order. The format string is byte-identical (objcheck, below). The game.log pattern has no source field (`[time] [warning] [core] [tid] msg`, e.g. `build/agent8/matrix/20261122-0509/runs/0509-sd-r1/game.log:414`). BindShader's `unrecognized_shader` probe and warning are unchanged (code identical, see Tests). Capture runs keep the full path (row "Default" above). |
| 6 | Locking: no new lock | **Deviation:** one leaf `std::mutex` (:271). See the section below. |
| 7 | Cap and invalidation | Cap 256 in total (:269); when full, stale entries are swept first (:312-315, :338); if it is still full, nothing is inserted and the full path continues as today. Forget-by-guest in `InvalidatePlacementShader` runs before the registry early return (:929); its callers are hooks_shader.cpp:65/:73, each followed by `RefreshPlacementShaderBinding` (:67/:75). Pool copies: miss spans are marked in `PoolCopyMayTouchShaders` (:981-985, key[1] = miss generation :963/:987), and overlapping entries are forgotten in `InvalidatePoolCopyShaders` (:1012), in the same place the registry drops resources. `ClearShaderMisses` runs in `ResetShaderResources` (:1123). |
| 8 | Sign-off on dropping the "bind calls" half of shader_archive.cpp:341-344 | Guest writes are covered by the stamp, pack loads by the generation, and readability by item 3. shader_archive.cpp is untouched (its per-lookup `hashes_by_size` memo stays). **Agent 10: please sign off.** |

## Item 6 deviation: the leaf mutex

- All callers already hold at least the registry half of `NativeRecordingGate` (native_worker.h:9-60):
  - `AdoptShader` via `LockRecording`;
  - `InvalidatePlacementShader` via `RegistryOnlyScope` (:926);
  - `PoolCopyMayTouchShaders` (:967-971).

  So the gate probably serializes them already. The mutex is belt-and-braces and costs about 20 ns uncontended.
- **It is a pure leaf.** Inside it there are only map operations, the lock-free `CpuMemoryUnchanged`
  (memory_watch.cpp:131-149) and `PrecompiledShaderPackGeneration` (an atomic load, shader_archive.cpp:134-136).
  It is never held across a guest query, a watch call or another lock.
- **Lock order** is registry→miss only: `PoolCopyMayTouchShaders` calls `ShaderMissEntries` under `g_registry_mutex`.
- `GuestRangeOverlapsPoolCopy` and `PoolCopyPhysicalRange` run outside it, on copied-out `shared_ptr<const>` entries
  (:391-402, :982-985).
- If Agent 10 prefers no mutex, the gate argument above has to become a proof for every caller pair in every worker
  mode. The gate's two halves are recursive and depend on the mode: a preparation scope takes only the registry half,
  and replay-only mode takes the recording half. I kept the 20 ns leaf lock instead of relying on that proof.

## Residuals (all keep the bind result the same: `nullptr`)

1. **Protect-only readability change, with no decommit** (so no watch callback fires):
   - (i) `readable < 8`: today the full path returns silently at :494. The cache instead replays the `fetch_add`
     and, if the counter is below 16, prints the line.
   - (ii) `readable` in 8-15: today words 2 and 3 print as 0; the cache prints the real cached words.

   Only the first 16 warnings are affected, because the counter is shared.
2. **Pool-copy ordering window:** the copy writes through host pointers before `InvalidateCpuPhysicalMemory`
   (hooks_buffer.cpp:190-198, :197) dirties the stamp. Registered resources have the same window, through
   `PlacementShaderUnchanged`'s `code_stamp`, so the cache is no weaker than the registry.
3. **Page-granular stamp:** any write to the page (both entries share page 0xED23D000) dirties the stamp. This only
   causes false invalidations (one full lookup, then the entry is remembered again), never false hits.

## OFF behaviour (must equal today)

- **`AdoptShader`:** two static-bool checks (:488, :499). `miss_arm` stays default, so `armed()` is false and nothing
  is remembered (:514).
- **`ShaderMissEntries`, `ForgetShaderMisses` and `ClearShaderMisses`** return early.
- **`PoolCopyMayTouchShaders`:** `g_miss_cache_generation` stays 0, so the footprint index rebuilds exactly when the
  registry generation moves, as before.
- **Static init:** the two empty maps, the mutex and the atomic add +72 instructions to `_GLOBAL__sub_I`. The span
  table is a function-local static and is never built when the cache is OFF.

## Tests (scratch, 1 clang at a time, BelowNormal priority, no ninja)

| Compile (full `-c`, build/dev command) | exit | warnings | errors | obj bytes | s |
|---|---|---|---|---|---|
| v3 patched | 0 | 2 | 0 | 507,756 | 69 |
| v3 control | 0 | 2 | 0 | 443,339 | 36 |
| v2 patched (`-march=x86-64-v2`) | 0 | 2 | 0 | 505,211 | 40 |
| v2 control | 0 | 2 | 0 | 441,573 | 11 |

- **`warn-diff.txt`:** v2 and v3 both have an identical warning set (file, message, flag). Both warnings already
  exist in shaders.cpp.
- **`objcheck-v2.txt` / `objcheck-v3.txt`:** both ISAs give the same result. Functions are paired by name, with the
  anonymous-namespace tag and lambda/funclet numbers normalized. Their disassembly is compared with absolute targets,
  nops and padding dropped.
  - **383** functions are identical.
  - **7** differ **only** in spdlog `source_loc` `__LINE__` constants, and each one equals the control line mapped
    through the patch: `BindShader`, `ShouldSkipBoundPixelShader`, `ResolveBoundShader`, `CreateShaderResource`,
    `DumpMissingShader`, and `PollPrecompiledShaders` plus its catch funclet.
  - **12** have code changes. These are exactly the patched functions plus their EH funclets: `AdoptShader`,
    `InvalidatePlacementShader`, `PoolCopyMayTouchShaders`, `InvalidatePoolCopyShaders`, `ResetShaderResources`,
    `_GLOBAL__sub_I_shaders.cpp`.
  - **55** are added: the new helpers plus their std, spdlog and `LongProbeEvent` instantiations.
  - **3** are removed: the old `log_<const char*, uint&, const uint&, u64, uint×4>` instantiation. It is replaced by
    `log_<const char*, uint&, uint&, u64&, const uint&×4>`, which has the same value types in the same order and the
    same format string.
  - **`.rdata` strings:** apart from the scratch source path, there are only 4 new strings and none removed:
    `LEGO_NATIVE_SHADER_MISS_CACHE`, `shader_miss_cache_insert`, `prefix=` (a probe field), and the helper's
    function name (a `source_loc` field, which is not printed).
- **Not run:** there is no unit fixture for shaders.cpp, and no build or game run tonight. The runtime proof is the
  test plan below.

## Expected gain

From `perf-notes/agent7-present.md` §3, n-prof: `BindShader` takes 6.10 of 12.36 ms/f of render-thread CPU. That
splits into `FindShaderByMicrocode` 3.10 and `ReadableGuestSpan`→`QueryRegionInfo` 2.88.

- A hit skips both, so the upper bound is about 5.98 ms/f.
- What remains per bind: `FindResource`, the header `ReadableGuestRange` (:456), the type check, one mutex plus hash
  lookup, an atomic load, and a one-page stamp compare. The real gain is therefore below that bound; measure it in
  window 4.

## Test plan (later; needs Agent 2's build and Agent 8's slot)

1. Agent 2 does an incremental build (shaders.cpp only), after Agent 10's S4 rating and Agent 1's GO.
2. Functional ON/OFF pair on the same bin and route, with `LEGO_NATIVE_TRACE_DIR` set. Expect:
   - logdiff NEW 0 / MORE 0;
   - the same draws/frame and marks;
   - the same `unrecognized_shader` probe events;
   - `shader_miss_cache_insert` events for 0xAC449538 and 0xAC448F28 when ON, and none when OFF.
3. OFF against the pre-patch bin: the same logs (OFF equals today).
4. Window-4 timing A/B with the user: render-thread ms/f and `BindShader` share, using n-prof.

## Asks for Agent 10

An S4 rating, acceptance of the item-6 deviation (or a request to drop the mutex), and the item-8 sign-off.
