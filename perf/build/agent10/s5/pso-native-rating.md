# S5 native PSO diffs 2.2 / 2.3 (M16): rating

M10, 2026-11-25 ~17:45. Read-only review. No build, no run, no repo writes (`git apply --check` only).

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent16/pso/pso-prepare-merged.diff (2.2) | 36ED6E02EAE588C7 | 6158 |
| build/agent16/pso/pso-unlocked-aux-save.diff (2.3) | 5CFD12E8C48C5295 | 10419 |
| build/agent16/pso/README.md | DFC22FDCE691B0DA | 10492 |
| build/agent16/pso-async/AB-PLAN.md (2.4, plan only; not rated here) | 87516A3952A239DD | 10166 |
| scratch/before/.../pipeline_library.cpp (HEAD) | EACB098E313E13AD | 31776 |
| scratch/both/.../pipeline_library.cpp (HEAD+2.2+2.3) | 486D82D09594FB63 | 38981 |

Base: DimensionsRecomp HEAD a8e8dc8. Blob `HEAD:rexlego/src/gpu_native/pipeline_library.cpp` = 4484038 (matches the diff index lines).
Re-run by me: `git -C DimensionsRecomp apply --check` gives exit 0 for both diffs. Worktree `gpu_native` is clean.
Also read at HEAD: pipeline_parallel.h (RunOrdered), pipeline_snapshot.h, pipeline_stats.h (OnAuxiliary), and the aux callers depth_resample.cpp L63 and native_overlay_gpu.cpp L103.

## Verdict

- **2.2 pso-prepare-merged: SAFE.** The default (threads=1) path is the HEAD code. The threads>1 path is correct, including the device-removed / `seed_names_` edge.
- **2.3 pso-unlocked-aux-save: SAFE-IF A1.**
  - The unlocked Save (`LEGO_NATIVE_PSO_SAVE_UNLOCKED=1`, default off) is sound as written. Its accept test is the right guard.
  - **A1 (required): gate the unlocked aux compile behind an env, default off.** This answers the Overseer's question: yes, gate it. Reasons are under 2.3 (a) below.
- **Build/run of a bin with these diffs: SAFE-IF B1-B4.**

## What I checked

### 2.2 (Prepare / PrepareParallel)

1. **threads == 1 is HEAD.**
   - The only edits in `Prepare()` are: the `threads > 1` early return is removed from the `prepare` lambda, and the outer call becomes `if (threads > 1) PrepareParallel(...) else if (prepare(recipes_)) {seed loop}`.
   - With threads==1 the lambda and the seed loop run unchanged. `PreparationThreads()` still defaults to 1.
2. **Job list and pointers.**
   - All seeds are read into `std::vector<Seed>` first. Jobs are queued only after that vector is final, so `&seed.recipes` stays valid.
   - Jobs hold (source pointer, entry index, name), and workers call `Describe(*Entries()[entry])` by index.
   - Workers touch only const recipes, `root_` and `PrepareOne`, which are the same thread-safety assumptions as HEAD.
   - `queued` dedups across all sources, so no two workers ever load one name. That is the D3D12 rule, and it is stronger than HEAD, which deduped per source plus `prepared`.
3. **Commit order.** RunOrdered commits in index order on the calling thread: local recipes, then seeds in `SeedPaths()` order. Library store order, `warmed_` first-512 residency and totals are therefore the serial sequence for the same set of successful names.
4. **Device removed (`stopped`).**
   - RunOrdered stops after the first `commit()==false` and discards in-flight results (pipeline_parallel.h header and L118-121), so `stopped` is set exactly once.
   - Seeds with `first > stopped` are skipped. This matches HEAD:
     - stop inside the local recipes: every `seed.first >= #local jobs > stopped`, so no seed is recorded, as at HEAD where `prepare(recipes_)` returned false;
     - stop inside seed k: seeds 0..k are recorded;
     - an empty seed (all names already queued) before the stop is recorded, as HEAD would have done.
   - Because `prepared` only grows and each name is attempted once, `prepared ∩ seed_k` at the end equals HEAD's per-seed snapshot. The one exception is a name that failed and would have been retried, which is the documented difference.
   - "removed N seeded pipelines" therefore keeps HEAD's semantics.
5. **Documented differences (threads>1 only):**
   - a failed name is not retried from a later source (same name means same desc hash, so this is acceptable);
   - all seeds stay resident during replay;
   - the "using startup pipeline seed" lines move ahead of the replay and are now printed even if the local recipes hit device-removed.

   All three are acceptable. A `failed=` count lower than HEAD at the same thread count is expected, not a regression.

### 2.3 (Auxiliary, Save, Open)

**(a) Unlocked aux compile (always on in the diff).**

The code is correct:
- the load and the hit/miss counters stay under `mutex_`;
- `CreateGraphicsPipelineState` runs unlocked and touches no library state;
- `Store()` re-takes the lock;
- a duplicate compile leads to a second `StorePipeline` failure, which `Store()` already ignores (no `stored`/`unsaved_` bump, HEAD L512-519);
- each caller still gets its own valid PSO;
- `pso_stats::OnAuxiliary` now runs outside `mutex_`, which is fine because its counters are atomics (pipeline_stats.h L54, L254-264).

**I still require a gate (A1),** because:
1. S4 practice is that new behaviour lands default off. The other two behaviours in this pair (PREPARE_THREADS>1, SAVE_UNLOCKED) already follow it.
2. The gain is only expected with lazy aux creation or PRECOMPILE=0 (README L74-78). At the shipped default (PRECOMPILE on, aux built at device init) there is nothing to win, so always-on buys risk with no measured benefit.
3. It changes concurrency on the draw path (DepthResampler::Create, overlay `Pipeline()` for a new format): duplicate compiles and a new interleaving with `Load()`/`Store()`/Save.
4. With a gate, a default-env run of the new bin is behaviourally HEAD (apart from the fingerprint), so the functional row's "N=1 / env unset must match HEAD" criterion is clean. The A/B needs no second bin.

The cost is about 5 lines: a `LEGO_NATIVE_PSO_AUX_UNLOCKED` getenv latched in `Open()` like `save_unlocked_`, and `if (!aux_unlocked_) {HEAD body}`. Use its own env, not `SAVE_UNLOCKED`, so the two effects can be attributed separately.

**(b) SnapshotUnlocked (env on).** I traced the loop:
- pass 1: query plus counted, then allocate `Capacity(size)` zero-filled outside the lock;
- pass 2: re-query, and Serialize unlocked if the size fits;
- accept under the lock only if `SUCCEEDED && GetSerializedSize()==size`;
- a dirty buffer is never reused; a fresh zeroed buffer is used each time, which keeps the NVIDIA unwritten-bytes rule (pipeline_snapshot.h);
- at most 3 Serialize attempts (`passes >= 6`), then `give_up()`, which frees the buffer before the locked fallback, so peak memory stays at one buffer;
- a non-E_INVALIDARG failure goes straight to the locked fallback;
- kNoMemory goes through the existing "save postponed" path.

The accept test is the real guard and does not depend on the driver returning E_INVALIDARG:
- every successful `StorePipeline` grows the serialized size;
- a store before Serialize either fails Serialize or changes the size;
- a store during or after Serialize changes the size before the re-lock.

So an accepted copy cannot be missing a counted store. `unsaved_ -= min(unsaved_, counted)` with `counted` from the same pass as `size` is correct. A size-identical race would need a store that adds no bytes, i.e. a failed duplicate, which is harmless. The bytes and the write path are the same as the locked code, so the file is byte-identical without a race.

**(c) Env off.** Save runs `SnapshotPipelineLibrary(mutex_, query, copy)` with the same lambdas, only hoisted into `query`. `save_unlocked_` is a plain bool written once in `Open()` before any save thread exists.

**(d) Lock order.** The only locks are `mutex_` and RunOrdered's internal mutex, never nested. The aux path takes `mutex_` twice, not nested.

## Conditions

- **A1 (2.3, required before any build that ships or times this):**
  - the aux unlocked compile goes behind its own env (suggested `LEGO_NATIVE_PSO_AUX_UNLOCKED=1`), default off and latched once;
  - unset means the HEAD body exactly;
  - re-issue the 2.3 diff with a new sha. I will re-check only that hunk.
- **B1:** build into a separate bin dir by the rated final2 method:
  - gpu_native TU only;
  - pe-check exports NEW==REF;
  - record a MANIFEST with the diff shas;
  - never write pinned bins (nativefinal2-bin, native4b*, devoff4b*).
- **B2 (fingerprint):** any gpu_native edit changes `LEGO_NATIVE_GPU_FINGERPRINT`, so the first boot of the new bin is cold. Compare warm with warm, never a warm HEAD cache with this bin (AB-PLAN §2 rule).
- **B3:** defaults stay off: PREPARE_THREADS=1, SAVE_UNLOCKED unset, AUX_UNLOCKED unset. Change a default only after the README functional row passes:
  - 2.2: L+C equal, F ≤ HEAD, same seed and "removed" counts;
  - 2.3: zero "gave up" lines, file loads on reboot, X/Y < Z.
  - Then apply a timing gate, which needs its own rating.
- **B4:** SAVE_UNLOCKED stays NVIDIA-only evidence. Concurrent Serialize on vkd3d/AMD/Intel is unverified (README L108-109). Don't make it default anywhere without that check.

## Findings

- **SHOULD S1 (2.3, Stop/Save race widened):**
  - `Stop()` waits for `saving_` to go false and then calls `Save()` without claiming `saving_`. A `Frame()` that runs after that check can start a second save thread.
  - At HEAD both Serializes run under `mutex_`. With SAVE_UNLOCKED=1 two Serializes can run concurrently on one library, and two writers then race on `native-pso.bin.tmp`.
  - The race is pre-existing (the tmp-file race) and needs `Frame()` after `Stop()`.
  - Suggested fix: in `Stop()`, spin on `saving_.compare_exchange_strong(false, true)` before `Save()`.
  - Not a blocker for an env-off build. Fix it before SAVE_UNLOCKED is used in timing rows.
- **NIT N1 (2.2):** seed memory is now the sum of all seed files (each ≤ kMaxRecipeFileBytes), and the seed dir can hold any number of `.bin` files. In practice there are 1-2. A total cap or a log of the total bytes would make it explicit.
- **NIT N2 (2.2):** `PrepareParallel` takes `prepared` by non-const reference but only reads it. It could stay `const&`.
- **NIT N3 (2.3):** the "gave up" line is INFO. WARN would match the README's "report the count" criterion and make it greppable alongside the other save warnings.
- **NIT N4 (2.3):** the doc's "duplicate compile costs CPU only" also means two different `ID3D12PipelineState` objects for one aux name across callers. That is fine for the current callers, which cache their own PSO; note it in the code comment.
- **Not rated:** AB-PLAN.md (2.4) is a run plan with no code. If its arms are run, they need the usual window/launcher rating.
