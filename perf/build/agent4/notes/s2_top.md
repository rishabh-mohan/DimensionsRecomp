> **RESUME (session 2, 19:50 on 2026-11-21).** Task #3's required work is done, compile-checked and tested. §S2 below is the session-2 report.
> - **Done:**
>   - default-path items 5, 6, 4 and 1;
>   - the SSE2 `#else` for the snapshot paths;
>   - opt-in redundant-state elision: `LEGO_NATIVE_ELIDE_STATE_CALLS=1`, **OFF by default**;
>   - 12 new columns in the `LEGO_NATIVE_STATE_CALLS` CSV;
>   - Agent 7's `HostDevice::PaceFrameBeforeLock()` call in SwapHook.
> - **Re-checked at 19:45 on the final tree, all as expected:**
>   - device.cpp syntax check: exit 0;
>   - the 26 fixtures: the same 9/26 as base, with an identical failing set;
>   - `run_patched.py`: 3/3 on base and dev.
> - **Left, in order:**
>   1. the Agent 5 registry diff (§1.2);
>   2. optional: a real-D3D12 per-call bench;
>   3. threaded items T1–T13 (§2);
>   4. `@@done 3`.
> - **Never:** run ninja in build/dev, or use more than 2 threads. Only `env/compile-one.ps1 ... -Db build/dev/compile_commands.json -SyntaxOnly`.

**Status (session 2): default path DONE. Elision DONE, opt-in. Threaded path NOT STARTED.**

§0-§7 below are the session-1 analysis (12:xx), kept as written. Their draw.cpp line numbers are from before the session-2 edits; §S2 has the current ones.

---

## S2. Session 2: changes, verification, numbers, in-game A/B plan

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/`, with line numbers from the current tree (draw.cpp is 5,719 lines). All benches: clang 23 from devshell, `-O2 -march=x86-64-v3`, at most 2 threads, median of 5 run medians. Bench and test sources are in `bench/agent4/`; results are in `build/agent4/`.

### S2.1 Changes for the 20:15 batch

| File | Change | Default behaviour | Header edit? |
|---|---|---|---|
| draw.cpp | items 5, 6, 4; SSE2 `#else`; elision; 5 new diagnostic hooks; SwapHook pacing call | identical | — |
| queries.cpp | item 1: `std::atomic<size_t> active_queries` | identical | — |
| long_probe.h | `LongProbeEnabled()` goes through `CachedProcessFlag` | identical | **yes, included by 7 TUs:** buffers, device, draw, hooks_portrait, queries, shaders, textures.cpp. It is not one of the 101 SDK headers in the generated-code closure |
| state_call_diagnostic.h | 12 new counters and CSV columns | identical (capture off unless `LEGO_NATIVE_STATE_CALLS` is set) | yes; draw.cpp only |
| draw_cached_flag.h (new, 24 lines) | `CachedProcessFlag<Read>()` | — | new; draw.cpp and long_probe.h |
| draw_log_throttle.h (new, 16 lines) | `TakeLogBudget(counter, limit)` | — | new; draw.cpp only |
| draw_state_shadow.h (new, 57 lines) | `DrawStateShadow` (std-only) | — | new; draw.cpp only |

| Variable | Default | Effect |
|---|---|---|
| `LEGO_NATIVE_ELIDE_STATE_CALLS` | unset → off. Only the exact value `1` enables it (`_dupenv_s`, read once) | Inline draws skip `setIndexBuffer` / `SetNativeBlendFactor` when the shadow proves the same value is already bound on the same recording (§S2.5) |
| `LEGO_NATIVE_STATE_CALLS=<csv>` (`_TRIGGER=<file>` optional) | unset → off | Unchanged semantics. The CSV gains `framebuffer_*`, `index_*` (incl. `index_skipped`), `blend_*` (incl. `blend_skipped`), `viewport_*` and `scissor_*`: 28 columns. The first 16 are as before |
| `LEGO_NATIVE_UNLOCKED_PACING` | unset → no-op | Agent 7's switch. It is read by `HostDevice::PaceFrameBeforeLock()`, which SwapHook now calls; unset, it returns before taking any lock |

> [!NOTE]
> One log-only difference (STATUS decision 5): the three per-draw "log the first N" throttles no longer print again after their u32 counter wraps. That would take 2^32 draws, about 10 h at 120k draws/s.

### S2.2 What changed, where

| Item | Where | What | Risk |
|---|---|---|---|
| 5 log throttles | draw_log_throttle.h:12-14; draw.cpp:2746, 2844, 3638 | `TakeLogBudget`: a relaxed load, then `fetch_add` only while under budget. It returns true for exactly the first N calls, as before | none |
| 6 diagnostics | draw_cached_flag.h:13-22; draw.cpp:437-438 (`TimingEnabled`, `PortraitProbeOn`), 445 (`DrawTimer(preparation)`), 479 (`ConstantTimer`: `TimingEnabled() && !t_preparing_draw`), 2481, 4760; long_probe.h:29-31 | Each process-constant flag is cached in a constant-initialised atomic byte (0 off, 1 on, 2 unread). Off costs one byte load and one predictable branch: no init guard, no call | none: the underlying flags were already process-constant statics |
| 4 TLS accessors | draw.cpp:128, 135, 142, 319, 427 (`Select_g_*(preparation)` overloads); 886 and 2461 (one `CurrentDrawPreparation()` per function) | The `g_*` macros resolve through the hoisted pointer. `t_draw_preparation` cannot change inside a draw.cpp function | low |
| 1 QueryDrawScope | queries.cpp:40 (counter), 114 (BEGIN), 125 (END, only while `queries` still maps to this query), 211 (Release), 230 (lock-free fast path, acquire), 234 (re-check under the lock), 311 (Reset) | The counter is maintained under `mutex`. The O(n) `none_of` walk is gone | low-med |
| AVX2 fallback | draw.cpp:3861, 3921, 3955 (`#if defined(__AVX2__)` … `#else` SSE2) | The AVX2 branch is the original text. The SSE2 branch makes identical bytes | none |
| Elision | draw_state_shadow.h; draw.cpp:583-653 (helpers), 2867 (lookup), 2947 (blend guard), 3549 and 3576 (index-buffer guards) | §S2.5 | opt-in only |
| Diagnostic columns | state_call_diagnostic.h:18-23, 26-37, 81-102, 150-172; draw.cpp:2671 (framebuffer), 2986-2991 (viewport, scissor) | Adjacent-equal counts plus elided-call counts | none (off by default) |
| Pacing hook (Agent 7) | draw.cpp:5344 | `HostDevice::PaceFrameBeforeLock()` between `PollCompletionCallbacks()` and `LockRecording()`. Reviewed: device.h:159-161, device.cpp:1855-1874 | none while `LEGO_NATIVE_UNLOCKED_PACING` is unset |

The session-2 diff vs `baseline/` is in `build/agent4/session2-diff.patch`. It is regenerated at the end of the session.

### S2.3 Verification

**Compile** (`env/compile-one.ps1 -Db build/dev/compile_commands.json -SyntaxOnly`, Release flags; logs in `build/agent4/compile/`):

| TU | `-march` | Result |
|---|---|---|
| draw.cpp, final (elision + pacing) | x86-64-v3 | exit 0; 71 warnings, all CRT `getenv` deprecation (`draw.pace.v3.log`) |
| draw.cpp with elision | x86-64-v2 | exit 0, 71 warnings (`draw.elide.v2.log`). The pacing edit is ISA-neutral |
| queries.cpp | x86-64-v3 | exit 0, 2 warnings |
| buffers.cpp, hooks_portrait.cpp, shaders.cpp, textures.cpp (long_probe.h includers) | x86-64-v3 | exit 0 |
| device.cpp (long_probe.h includer) | x86-64-v3 | exit 0 at 19:45 (`device.cpp.v3.recheck.log`). The earlier exit 1 was the then-missing generated `copy_color_ps.h` |

**Tests:**

| Test | Covers | Result |
|---|---|---|
| `bench/agent4/test_snapshot_simd.py --bench` | SSE2 vs AVX2 snapshot | PASS. v3 codegen identical to base (3,078 asm lines); SSE2 output byte-identical. AVX2 1,417 / 2,805 / 2,340 ns vs SSE2 2,870 / 4,525 / 3,426 ns (3 snapshot shapes) |
| `bench/agent4/run_fixtures.py` (26 gpu-aot fixtures) | everything they extract | Base and the final dev tree pass the **same** 9/26, with an identical failing set (re-run at 19:45, `build/agent4/fixtures-dev2/results.json`). The 9: buffer_variants, long_probe, portrait_probe, snapshot_selection, submission_waits, temporal_draw_route, texture_depth_upload, texture_source_residency, texture_use_refresh. The other 17 were already failing on base because their fakes are stale |
| `bench/agent4/fixtures/run_patched.py` (patched copies of test_constant_timing, test_query_sample_pool and test_query_retirement; see the README there) | items 6, 4, 1 | 3/3 PASS on base and dev (re-run at 19:45); 8/8 one-line mutants caught |
| `bench/agent4/test_state_call_diagnostic.py` | new ledger columns | PASS; negative control PASS |
| `bench/agent4/test_viewport_shadow.py` | viewport/scissor ledger | PASS |
| `bench/agent4/test_state_shadow.py` | elision (extracts draw.cpp:583-653 verbatim) | **OK: 20 runs, 19 audit checks.** 7/7 real cases, 13/13 mutants killed, 19/19 static audit checks |

`test_state_shadow.py` in detail (`build/agent4/state_shadow/results.md`):
- **Unit:** key changes; size, format and bitwise blend compares; gates. These cover the preparation gate, the full-preparation gate and the exact `"1"` parse.
- **Oracle:** 180,650 random draws against a simulated plume list, including:
  - list begin/end with serial bumps, layout and root-signature changes, SetDescriptorHeaps;
  - raw writers that call both plume notifies, or only one of them.

  The oracle checks that the D3D12 state the list ends up with, draw by draw, is the same as without elision. With elision on, 91,974 index-buffer and 92,479 blend calls were elided. With the variable unset, 0 were.
- **Negative controls:** these are contract violations (§S2.5), and the oracle must catch each one (exit 3):
  - the lookup moved after the layout bind;
  - a raw write with no notify;
  - a draw-layout rebind after a raw write.
- **Mutants**, all killed: no tripwire; ignore the serial; ignore both; no heaps check; no root-signature check; full-preparation gate removed; preparation gate removed; loose env parse; shadow ignores size; shadow ignores format; float (not bitwise) blend compare; Invalidate keeps blend; Begin ignores layout.
- **Static audit** of the live tree: every IB and blend writer in rexlego/src, and the plume begin/end/notify/flag semantics the tripwire relies on (list in §S2.5).

**Already-failing fixtures and the elision edit** (also in `bench/agent4/fixtures/README.md`): draw_index_bounds, shader_binding_failures and cull_state fail on base too. They now also meet `SameDrawIndexBuffer(draw_shadow, …)` and one more `CullDrawScissor(` use (draw.cpp:2988, the scissor diagnostic) in the extracted DispatchDraw text. Once their stale fakes are fixed, they need two stand-ins:
- `DrawStateShadow* draw_shadow = nullptr;`
- `template <class... A> bool SameDrawIndexBuffer(A&&...) { return false; }`

### S2.4 Numbers

Default path (`python bench/agent4/run_benches.py --runs 5`; `build/agent4/bench/results.md`). Other agents kept the CPU at 48-100% load, so absolute values are noisy. The before/after ratios are the result.

| Bench | Case | Before (ns) | After (ns) |
|---|---|---:|---:|
| log_throttle (3 sites per draw) | 1 thread | 34.2 | 1.75 |
| | 2 threads | 157.3 | 1.81 |
| cached_flag (5 flag calls + 20 LongProbe checks per draw) | per draw | 47.0 | 15.2 |
| | `TimingEnabled()`, one check | 2.35 | 0.68 |
| tls_accessor | no preparation: 12 → 3 accessor calls | 92.6 | 23.5 |
| | preparation: 14 → 3 calls | 82.4 | 37.2 |
| | for reference: 12 calls with Agent 7's inline accessor | — | 55.1 |
| query_scope | N=0 live queries, 1 thread | 44.0 | 2.50 |
| | N=16, 1 thread | 65.6 | 2.32 |
| | N=64, 1 thread | 164.9 | 2.13 |
| | N=256, 1 thread | 1,131 | 2.25 |
| | N=256, 2 threads | 2,476 | 2.35 |

The default path in isolation saves about **175 ns per draw** with no live queries (32 + 32 + 69 + 42), and more as live queries grow: up to 1.1 µs at N=256. That is about 0.18 ms of render-thread CPU per 1,000 draws. The in-game A/B (§S2.6, A1) decides the real figure.

Elision cost (`test_state_shadow.py` bench, ns per draw, median of 5; `build/agent4/state_shadow_bench_run1.md`). In this harness the two D3D12 calls are fakes costing about 1 ns.

| `LEGO_NATIVE_ELIDE_STATE_CALLS` | direct (no gate) | gated, repeated state | gated, changing state |
|---|---:|---:|---:|
| unset | 4.1 | 6.1 | 6.1 |
| 1 | 5.4 | 17.6 | 21.2 |

- **Off:** +2 ns per draw. The same direct code differs by 1.3 ns between runs, so this is at the noise floor.
- **On:** the shadow costs about 12-16 ns per draw more than the fakes. It pays off when each skipped real `IASetIndexBuffer` / `OMSetBlendFactor` (plume virtual call, D3D12 runtime, driver recording) costs more than about 6-8 ns. That cost is unmeasured.
- If the A/B is marginal, the conservative per-call re-check inside `SameDraw*` (`CheckInlineStateShadow`) can go. It is redundant today.

### S2.5 Redundant D3D12 state-call elision (STATUS decision 2)

**Scope.** Elision skips only:
- `setIndexBuffer` (draw.cpp:3550, 3577);
- `SetNativeBlendFactor` (draw.cpp:2948 → native_recording.cpp:534/542).

It applies only to inline draws: no `DrawPreparationContext`, full preparation off, and the list must be a `plume::D3D12CommandList` (`dynamic_cast`; prepared/tape lists bypass it).

These two states are safe to shadow for three reasons:
- plume caches neither of them;
- D3D12 keeps both until the list sets them again or is reset;
- PSO, root-signature and descriptor-heap changes leave them alone.

Layouts, PSOs, descriptor tables and framebuffers are left to measurement (CSV) and plume's own `PLUME_D3D12_STATE_CACHE`.

**Key.** The shadow is keyed on (command list, recording serial, pipeline layout). `DrawStateShadow::Begin` forgets every bound value when the key changes.

**Tripwire.** The tripwire reuses plume's own `descriptorHeapsSet`, `cachedGraphicsRootValid` and `cachedGraphicsRootSignature`.
- These are cleared by `begin()`, `end()`, `notifyCommandStateWasChangedExternally()` and `notifyDescriptorHeapWasChangedExternally()`. Binding another root signature replaces the cached one.
- They are checked at the lookup (draw.cpp:2867, before `BindNativeDrawLayout` re-validates them) and again in each `SameDraw*`.

**Required invalidation points**, as STATUS decision 2 asks:

| Event | Caught by |
|---|---|
| list begin/reset | serial in the key, and the plume flags |
| root-signature change | layout in the key, and the cached signature |
| SetDescriptorHeaps | `descriptorHeapsSet` |

**The serial is required, not defence in depth.** After a list reset, the first plume layout bind before the first draw makes the flags valid again. Without the serial the stale shadow would survive (mutant `ignore_serial`: killed at oracle step 698).

**Why one global shadow, not thread_local.** Every DispatchDraw caller without preparation records under `LockRecording` or `NativeRecordingMutex`, so they are serialized. Full preparation replays tapes onto the same list, so it is gated off.

**Contract limits.** The tripwire cannot see two cases:
- a raw D3D12 writer that sets the index buffer or blend factor and calls neither plume notify;
- a raw writer that notifies and then rebinds the draw layout through plume before the next draw.

The negative controls show the oracle catches both. The audit shows neither exists today:
- the only raw `IASetIndexBuffer` is native_overlay_gpu.cpp:176. device.cpp follows the overlay with both notifies, then `setFramebuffer(nullptr)`, the PRESENT barrier and `end()`, with no draw between;
- `OMSetBlendFactor` appears only in native_recording.cpp: tape replay (:322) and `SetNativeBlendFactor` (:542);
- the other raw passes notify plume afterwards (device.cpp:1568-1577, 2021-2027, 2067-2077; temporal_present.cpp:257);
- there is no `ClearState`, `ExecuteBundle` or `ExecuteIndirect`.

**Rule for future raw-D3D12 code on the frame list:** call `notifyCommandStateWasChangedExternally()` afterwards. A follow-up could add an explicit `InvalidateDrawStateShadow()` hook.

**Viewport/scissor.** These are diagnostic only this round. Eliding them needs hooks in the helper passes that set their own viewport (phase 2), and only if the CSV shows enough repeats.

### S2.6 In-game A/B plan

Prerequisites:
- the NATIVE_GPU=ON dev exe and `build/baseline-bin`;
- Agent 3's boot procedure;
- the same save and a fixed camera path (or a static hub/menu scene);
- vsync off, the same resolution, FSR off;
- each measurement is the median of 5 runs × 60 s.

Never time with the CSV, `LEGO_NATIVE_TIMING` or the debug layer on. Those are correctness runs.

| Step | Run | Measure / compare | Pass |
|---|---|---|---|
| **A0** identity | dev vs base, default env. One extra run each with `LEGO_NATIVE_STATE_CALLS=<new file>` (it refuses to overwrite) | Screenshot diff; D3D12 debug layer; PIX one-frame API call list; CSV columns 1-16 per frame in a static scene | identical |
| **A1** default-path CPU | dev vs base, default env; then one run each with `LEGO_NATIVE_TIMING=1` | Frame time and render-thread CPU; per-draw timing | dev ≤ base. Expect about 0.1-0.2 ms per 1,000 draws |
| **B1** redundancy ratio (measure first) | dev, `LEGO_NATIVE_STATE_CALLS=<csv>` (optionally `_TRIGGER=<file>` to arm a chosen 120-frame window) | Per frame: `index_equal/index_calls` and `blend_equal/blend_calls` (the elision upper bound); also the `layout`, `pso`, `table0-3`, `framebuffer`, `viewport` and `scissor` `_equal` ratios for later rounds | Go to B3 only if index + blend repeats are a large share (≳30%) of those calls |
| **B2** plume cache (separate axis, not mine) | dev, `PLUME_D3D12_STATE_CACHE=1` vs unset | Frame time; plume prints "Plume D3D12 command state cache: enabled" | — |
| **B3** elision | dev, `LEGO_NATIVE_ELIDE_STATE_CALLS=1` vs unset; then one correctness run with the CSV, the debug layer and PIX | Frame time. `index_skipped ≤ index_equal` and `blend_skipped ≤ blend_equal`. PIX: every remaining call identical and in order; each missing call an exact repeat of the value already bound. Screenshot diff; debug layer | zero image diff, zero new debug-layer messages, win larger than run-to-run noise |

Elision stays OFF by default. Turning it on needs both B3 and an Agent 1 ruling.

### S2.7 Cross-owner status

- **Agent 7:**
  - the `PaceFrameBeforeLock()` call is applied and compile-checked;
  - the `CurrentDrawPreparation` inline diff was sent (device.h:93 becomes `extern thread_local` plus an inline accessor; device.cpp:756 is deleted). Agent 7 plans it for a batch after 20:15, as its item (h). Bench: 12 accessor calls 92.6 → 55.1 ns on its own; it stacks with the draw.cpp hoist.
- **Agent 5:** registry lookup diff (§1.2), not sent yet.
- **Agent 6:** no async-PSO hook request received.

### S2.8 Not done

- Threaded items T1–T13 (§2): not started. The brief allows them only after the default path.
- Item 8 (the SetTexture flag hoist, hooks_state.cpp): not started.
- The per-call cost of real D3D12 `IASetIndexBuffer` / `OMSetBlendFactor`. It would size the elision win before the in-game A/B.

---

## Session 1 analysis (12:xx; line numbers are from before the session-2 edits)
