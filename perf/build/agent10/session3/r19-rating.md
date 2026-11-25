# #19 rating: R1 stage 2, async submit (cvar `d3d12_async_submit`)

M10 (successor of Agent 10), session 3, task S3T-10. Read-only work on 2026-11-25, 00:55-01:45: nothing was built or run. The diff was re-applied only to a scratch copy of `orig/` (deleted afterwards).

**Files rated** (`build/agent7/s4-r1s2/`):

| file | sha256 (first 16) | lines |
|---|---|---|
| `RATE-REQUEST.md` | 1C2B8688A43ED4DC | 531 |
| `s4-r1s2.diff` | 06B0D371686CD384 | 446 |
| `NOTE.md` | 58E8EA9F80B1B667 | 285 |
| `PROOFS.txt` | FF360AC947439778 | 94 |
| `CHECKS.txt` | A5A8F777494D6C9E | 24 |
| `FUNCTIONAL-ROWS.md` | BB05AAFD0D6C4438 | 74 |
| `SOAK.md` | F6A340A23B0A28C7 | 44 |
| `queue-s4r1s2.jsonl` | 175723608FD20891 | 11 |
| `matrix-w7-draft.json` | 2A07C6593AFB937D | 45 |
| `SHA256SUMS.txt` | 8A38FD9D3CD8B375 | - |
| `soak-check/soak_check.py` | CAB5CB2CCA686C67 | - |
| `new/sdk/.../d3d12/command_processor.h` | EF0DC13DA29703C7 | - |
| `new/sdk/.../d3d12/deferred_command_list.h` | E7512824D8E6F967 | - |
| `new/sdk/.../d3d12/command_processor.cpp` | 05BBCE8B7E3FB27D | - |
| `new/sdk/.../d3d12/shared_memory.cpp` | 9E908D31E6F64A31 | - |
| `new/sdk/.../d3d12/texture_cache.cpp` | 4183887C9D625B97 | - |
| `deferred_command_list.cpp` (unchanged) | 30FF57446EFB5D76 | - |

Full diff sha256: 06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7.

Sub-report used: `build/agent10/session3/sub-r19-queueops.md` (E03648C61901A846, 158 lines; employee E10.1, queue-ops code read).

**Base.** `DimensionsRecomp/rexglue-sdk` HEAD is 5350b1de99... The 6 `orig/` files equal `git show 5350b1d:<path>`, the snap1 copies and the live worktree (LF; e.g. `command_processor.cpp` 027204B53A271D69). The only SDK worktree changes are the `thirdparty/fmt` and `thirdparty/simde` submodule entries. `git -c core.autocrlf=false apply --verbose` on a scratch copy of `orig/` printed 5 "Checking patch" lines, applied all 5 cleanly, and the result is byte-equal to `new/sdk/`. Every `SHA256SUMS.txt` entry matches. M7's re-check against 5350b1d (`build/agent7/session3/check-19-5350.out.txt`, 5B0C07CC) agrees.

## Verdict

- **(a) Build into devoff4b as a default-off test bed: SAFE.** OFF is inert (see below). Build conditions:
  1. Order as in RESUME: syntax check (RATE-REQUEST section 10.1) and before-hash check first; then copy `new/sdk/` over the 5 files (don't `git apply` on the non-repo tree without `-c core.autocrlf=false`, N2).
  2. `command_processor.h` changes the class layout, so this is a full SDK rebuild (≤2 threads, M2 only), not a relink.
  3. MANIFEST plus bincheck with the 3 needles; row a (OFF identity vs devoff4b) is the first run.
- **(b) Test ON (`d3d12_submit_split_kb=<N>` + `d3d12_async_submit=true`) in rows, soak and W7: SAFE-IF**:
  1. Stop at the first FAIL. Rows a and b (and i) pass before any ON row.
  2. Row g (debug layer) runs before soak e and before W7. Suggested order: a, b, i, c, g, j, d, f, e; W7 only after the rows and the soak pass (S1).
  3. ON rows only after the Overseer's RUN GO. A GPU fault or TDR can reset the shared GPU, so prefer a time when the user isn't gaming.
  4. Any hang or timeout is a FAIL. Triage starts from the `GPU Commands` stack (DrainAsyncSubmissions / full-ring wait) and the `D3D12 Submit` thread, not from F-CA. STUCK-LOCK is judged by the finding-10 rule. A 3 s shutdown-watchdog hit in an ON row is flagged even if the row otherwise passes.
  5. No combination with #33 ON, the CTR/counters build, native bins or resolution scaling without a re-rating (S2).
  6. `<N>` comes only from the ready-N gate (`build/agent3/s4b/ready-N`, absent at 01:40). Timing comes only from the user's double-click W7; agents run functional rows only.
- **(c) Threading/ownership rules (section 6) and code reads (section 11): ACCEPTED**, with the NITs below.
- No BLOCKER. 2 SHOULD, 8 NIT.

## What I checked

### OFF is inert
- Every new path is behind `if (submit_async_)`; the one ternary (cp.cpp new ~L4456) is reached only when a split is due. `ShutdownAsyncSubmit` returns early when the thread was never created; `SetupContext` resets the state.
- Compile plausibility (no compile done): the `DeferredCommandList` ctor keeps its default `initial_size_bytes = 1_MiB`; `deferred_command_list.h` includes `rex/assert.h`; `Thread::Create({}, fn)`, `set_name` and `rex::thread::Wait(handle, false)` match their use in `pipeline_cache.cpp` L161-182. DCL members are only `command_stream_` and `command_processor_`, so the new `Swap` is complete.

### ON: the split submission
- `EndSubmissionAsync` matches `EndSubmission(false)` for a split: allocator create (and fail-return) happens before the ring is touched; then pipeline-cache `EndSubmission`, `SubmitBarriers`, allocator bookkeeping, `++submission_current_`, `submission_open_ = false`, flag reset.
- Ring: predicates are mutex-guarded, no lost wakeups; a slot is freed only after Reset + Signal; the Submit thread takes only `async_submit_mutex_` and never waits on a fence, so non-draining fence waits on the GPU Commands thread always end.
- Drains: top of `EndSubmission` (L4306), `CheckSubmissionFence` with `>=` (L4024), `PublishOnDemandMemexport` (L3268, before the global lock), the flushes in `shared_memory.cpp` L492 and `texture_cache.cpp` L1255 (GPU Commands thread, no global lock held). `RetireOnDemandMemexport` waits only for batches published after a drain.
- Lifetimes: pipelines are destroyed only in `PipelineCache::Shutdown` (`pipeline_cache_.reset`, cp L2067), after `ShutdownAsyncSubmit` (L1974). `ShutdownShaderStorage` / `InitializeShaderStorage` don't destroy pipelines. `ClearCaches` sets `cache_clear_requested_`, which is handled inside `EndSubmission` after the drain and `AwaitAll`.
- E10.1's queue-ops read (Q1-Q4) confirmed: no other queue `ExecuteCommandLists`/`Signal` from GPU Commands while a chunk can be queued, except the presenter-owned ones listed in N3.

### F-CA (RESUME section 6 item 8)
F-CA is native-only: rexlego `gpu_native` th2 `RecordingQueue`, `HostDevice::RetireResource`, `LockRecording`. #19 is the SDK Xenos D3D12 path and takes no `LockRecording`; the rows and W7 use the devoff4b Xenos bin with no native env. So F-CA doesn't apply. Keep S2-6 (async submit off on native) and treat any native use as a new rating (S2).

## Findings

- **S1 (SHOULD).** Move row g (D3D12 debug layer, ON) ahead of soak e and W7. It is the only row that can catch a wrong-thread or wrong-state queue call that doesn't crash, and the soak is the expensive row.
- **S2 (SHOULD).** Combination guard. #33 hunk #5 (`CanEndSubmissionImmediately` no-wait) together with #19 ON would allow splits while pipelines are still being created; the drain/lifetime argument above assumes 5350b1d pipeline-cache behaviour. Re-rate before combining #19 ON with #33 ON, the counters build, native bins or resolution scaling. Write this into the queue notes.
- **N1.** Device-removed edge: a `UINT64_MAX` completed value could reclaim an allocator still referenced by a queued chunk. With FIFO order and a dead device this is harmless; a comment would help.
- **N2.** RATE-REQUEST section 2 and `CHECKS.txt` use `--directory=games/lego-dimensions-recomp/...`, stale now that the WS isn't inside a git repo; from the WS root the paths are cwd-relative. Under global `core.autocrlf=true`, `git apply` on a non-repo tree writes CRLF: use `-c core.autocrlf=false` or copy `new/sdk/` (M7's relay; NIT).
- **N3.** The section 6 table misses the tracker retry `Signal` (`d3d12_submission_tracker.cpp` L69-71), `CaptureGuestOutput` ECL + Signal (presenter L309-310, no caller) and the swap-chain create/resize/Present. All are presenter-owned and harmless (E10.1).
- **N4.** No thread-affinity assert in `Flush`/`Drain`; a debug-only assert would make S2-style misuse visible.
- **N5.** `Execute` reads CPU RTV/DSV descriptors on the Submit thread. That is safe today (they are immutable until a drained cache clear) but fragile; add a comment (E10.1).
- **N6.** `deferred_command_list.cpp` L89-90: the counters comment is stale, and its race exists only in the counters build (section 11.6).
- **N7.** `queue-s4r1s2.jsonl` row e note still says "tile-mapping flushes".
- **N8.** The extra default-priority Submit thread adds CPU load, and finding 10 is load-sensitive; read W7 deltas with that in mind.

## Read / Sent

Read: BRIEF-COMMON, RESUME sections 2, 6, 7; `build/agent10/HANDOFF.md`; all files in the table; `build/agent10/t27/sub-r21-coderead.md` (F-CA); SDK 5350b1d sources around every hunk. Sent: this verdict to the Overseer.
