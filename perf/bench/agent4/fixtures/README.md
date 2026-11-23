# Patched gpu-aot fixtures for Agent 4's draw-path edits

These are copies of `DimensionsRecomp/tools/gpu-aot/test_*.py`. The originals are untouched. Each copy takes
`--tree <DimensionsRecomp root>` (default: the dev tree `DimensionsRecomp/`), so one fixture runs on
`baseline/DimensionsRecomp` (before) and on `DimensionsRecomp` (after Agent 4's session-2 edits).

How to run them (one compile at a time):
- `. env/devshell.ps1 -Quiet; python bench/agent4/fixtures/run_patched.py [stems]` runs each copy on base, then on dev.
  Logs go to `build/agent4/fixtures-patched/{base,dev}/<stem>.log` and the summary to
  `build/agent4/fixtures-patched/results.json`. It also rewrites `<stem>.diff` (the copy vs the original, made with
  difflib). `--diff-only` only rewrites the diffs.
- To run a single fixture: `python bench/agent4/fixtures/<stem>.py --tree baseline/DimensionsRecomp build/agent4/fixtures-patched/base/<stem>`
  (or `--tree DimensionsRecomp build/agent4/fixtures-patched/dev/<stem>`).
- `python bench/agent4/fixtures/mutants.py` builds 8 one-line mutants of the dev sources (copies under
  `build/agent4/fixtures-patched/mutants/<id>/tree`). Each one must make its fixture fail. Results are in
  `build/agent4/fixtures-patched/mutants/results.json`.

## Results

| fixture | original base / dev (clang errors) | patched base | patched dev | what changed vs the original, and why |
|---|---|---|---|---|
| test_constant_timing | FAIL 1 / FAIL 4 | PASS | PASS | **stale:** `t_preparing_draw` fake. **agent4:** `DrawPreparationContext`, uncached `TimingEnabled()`, `Select_g_draw_timing(preparation)`, and the `MakeDrawTimer()` constructor helper. **Added:** prepared-draw and preparation-worker checks. |
| test_query_sample_pool | FAIL 5 / FAIL 7 | PASS | PASS | **stale:** 2-arg `QueryDrawScope`, `RecordNativeCommand`, `(samples, scale)` draws. **agent4:** `active_queries`. **Added:** no-lock fast-path checks, the END case, and the counter invariant. |
| test_query_retirement | FAIL 15 / FAIL 18 | PASS | PASS | **stale:** worker/stage/gate fakes, `summed`/`sum`, pair draws, and the cached-sum adaptation. **agent4:** `active_queries`. **Added:** counter invariant after every step, END racing Release/Reset, and the recorder-barrier stage. |
| test_quad_buffer_windows | FAIL 20+ (error limit) / FAIL 20+ | not patched | not patched | Stale far beyond the time box (see below). Agent 4 adds only the undeclared `preparation`. |
| test_nonindexed_buffer_windows | FAIL 19 / FAIL 20+ | not patched | not patched | Same as quad. |

"stale" means the fixture was already broken at baseline: its fakes no longer match the real code in both trees.
"agent4" means the change is needed because of Agent 4's edits. All three patched copies keep every original
scenario and assertion. Only the calls were adjusted to the real signatures, and the one cached-sum adaptation is
explained below.

### test_constant_timing
- Both trees: `--tree`.
- Stale: `t_preparing_draw` is a `thread_local ParallelDrawWork*` in draw.cpp. It is faked with that type.
- agent4: `DrawPreparationContext` lives in device.h, which draw.h does not include, so the copy adds an empty fake
  in the same namespace.
- agent4: `TimingEnabled()` (draw.cpp:436) is `CachedProcessFlag<NativeTextureTimingEnabled>`. The fake forwards
  without caching because the fixture toggles the flag at runtime. In production the flag is process-constant.
- agent4: the plain `DrawTiming g_draw_timing` global is replaced, as in draw.cpp (both trees), by serial/prepared
  `DrawTiming`s. `Select_g_draw_timing(const DrawPreparationContext*)` picks one, and
  `#define g_draw_timing Select_g_draw_timing()` goes through `CurrentDrawPreparation()`.
- agent4: `MakeDrawTimer()` builds `DrawTimer(CurrentDrawPreparation())` when that constructor exists (dev) and
  `DrawTimer()` otherwise (base), via `if constexpr (std::is_constructible_v<...>)`.
- Added: a prepared draw counts and times into the preparation's `DrawTiming` and leaves the serial one untouched.
  This covers `DrawTimer(preparation)` and `Select_g_draw_timing(preparation)`.
- Added: with `t_preparing_draw` set and timing enabled, `ConstantTimer` samples no clock and adds nothing. This
  covers `TimingEnabled() && !t_preparing_draw`.
- The original toggle assertions still cover `DrawTimer::enabled = TimingEnabled()`.

### test_query_sample_pool
- Stale: the real constructor is `QueryDrawScope(plume::RenderCommandList*, double sample_scale)`. Calls pass 1.0,
  and the 300-draw loop passes 0.5 and asserts each recorded draw keeps 0.5.
- Stale: `RecordNativeCommand` is faked as running the command immediately, which is what the real helper does on a
  non-deferred list.
- Stale: `Query::draws` is `vector<pair<shared_ptr<Samples>, double>>`, as in queries.cpp, so the test uses `.first`.
- agent4: `active_queries` is faked as `std::atomic<size_t>`. The test counts it where it marks a query active (as
  BEGIN does) and uncounts it at the simulated END. `check_active()` asserts that the counter equals the number of
  active entries. It runs only on trees whose extracted text mentions `active_queries` (`kCountsActive`).
- Added: `std::mutex` is replaced by `CountingMutex`, which counts `lock()` calls. On dev, no lock is taken when no
  query is active: with an empty map, with a created-but-never-begun query, and after END. That covers the
  `QueryDrawScope` fast path. On base those scopes still lock and walk the map. Both trees assert that no scope
  opens.

### test_query_retirement
- Stale: `NativeWorkerStarted`, `NativeTaskStage`, and the 5-argument `NativeWorkerSubmit` from native_worker.h.
- Stale: `NativeRecordingGate`, faked as a recursive mutex like the old fake's recording mutex.
- Stale: `Query::summed`/`sum` and pair draws (queries.cpp, both trees), plus `<cmath>`/`<cstdlib>`.
- Stale: `GetQueryData` caches the sum after the first successful read (both trees). As a result, the original
  readback-failure assertion, which came after a successful read, could never fail. The copy first asserts that the
  cached value is returned without mapping again (new "cached sum" check). It then clears `summed`, so the failing
  readback is a first read. The saturation check is unchanged.
- `NativeWorkerStarted()` returns false. Queued tasks run inline here as on the recorder thread, so retires take the
  direct path. Returning true would re-queue into the vector whose task is running.
- agent4: `active_queries` fake. The copy adds `++active_queries` where the original marks a query active by hand
  (as BEGIN would); without it the real END would underflow the counter. `check_active()` runs after every
  BEGIN/END/Release and every queued task.
- Added: `ResetQueryResources` is extracted too. A one-shot hook in the query mutex runs a step just before END's
  second critical section, modelling the full-preparation interleavings:
  - The final Release runs there. END returns kInvalid, the query is neither active nor ended, and the count stays
    consistent.
  - `ResetQueryResources` runs there. END still signals, but it does not uncount the dropped generation (dev's
    `it->second == query` guard), so the count stays 0.
- Added: both queued BEGIN/END tasks are submitted as `kRecorderBarrier`. The fast path's ordering argument
  (queries.cpp:37-39) depends on this barrier.

### Mutation check (`mutants.py`, all CAUGHT)
| mutant (dev source edit) | fixture | failing assertion |
|---|---|---|
| ConstantTimer `TimingEnabled() && !t_preparing_draw` -> `TimingEnabled()` | constant_timing | `FakeClock::calls==sampled` |
| DrawTimer `enabled = TimingEnabled()` -> `true` | constant_timing | `g_draw_timing.calls==1&&FakeClock::calls==0` |
| `++Select_g_draw_timing(preparation).calls` -> `(nullptr)` | constant_timing | `g_draw_timing_prepared.calls==1&&...` |
| drop the unlocked `active_queries` early return in QueryDrawScope | sample_pool | `mutex.locks==locks` |
| drop `if (!slot \|\| !slot->active) ++active_queries` (BEGIN) | retirement | `active_queries==n` |
| END decrements without the `it->second == query` guard | retirement | `active_queries==n` (END racing Reset) |
| drop `if (released->active) --active_queries` (Release) | retirement | `active_queries==n` |
| drop `active_queries.store(0)` (Reset) | retirement | `active_queries==n` |

The second check under the lock (`active_queries.load(relaxed) == 0`) is not mutated. Removing it changes no
observable behaviour, because an empty consumer list returns right after.

### Not patched: test_quad_buffer_windows, test_nonindexed_buffer_windows
Both already fail at baseline with 19 to 20+ errors (clang stops at its error limit). Their fakes predate the
recorded-draw and multi-rate machinery: `RecordedMultiRateDraw`, `t_recording_draw`, the `multi_rate_fetch` member,
`multi_rate_draw`, and more past the error limit. Making them compile faithfully means re-faking those parts of
DispatchDraw, which does not fit the time box.

Agent 4's edit adds one error class: `preparation` is undeclared where DispatchDraw now uses the hoisted
`DrawPreparationContext* const preparation = CurrentDrawPreparation();`, with `Select_g_prepared_draw(preparation)`,
`Select_g_vertex_input_usage(preparation)` and `Select_g_quad_indices(preparation)`. Once the stale parts are fixed,
the suggested fake is `const DrawPreparationContext* preparation=nullptr;` plus, for each of the three,
`template<class P> auto& Select_g_quad_indices(P){return g_quad_indices;}`.

### Already failing on base: draw_index_bounds, shader_binding_failures, cull_state
These three fail on base and dev alike because their fakes are stale; the 19:45 re-run on the final tree has the same
9/26 passing set as base. Since the opt-in state-call elision (perf-notes/agent4-draw-path.md §S2.5), the DispatchDraw
text they extract also contains:
- `SameDrawIndexBuffer(draw_shadow, …)` around both index-buffer binds (draw.cpp:3549, 3576);
- one more `CullDrawScissor(` call (draw.cpp:2988, the scissor diagnostic). test_cull_state's ordering assertion
  still finds `commands->setScissors(CullDrawScissor(` first (draw.cpp:2971).

Once their stale parts are fixed, the stand-ins are `DrawStateShadow* draw_shadow = nullptr;` and
`template <class... A> bool SameDrawIndexBuffer(A&&...) { return false; }` (false means "issue the call", which is
what the default path does).
