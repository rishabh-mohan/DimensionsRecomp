# S5 rating: M2 zpd-log diag (occlusion-query counters for nops S1)

M10, 2026-11-25 18:33. Static review only (FREEZE active; nothing compiled or run).

| File | sha256/16 | Bytes |
|---|---|---|
| build/agent2/s5/zpd-log/zpd-log.diff | 2FB24916EA354EC0 | 8264 |
| build/agent2/s5/zpd-log/README.md | 13846094DDD4DB03 | 2712 |
| build/agent2/s5/zpd-log/check.txt | 2F29DFA4A8CBB48C | 1551 |
| build/agent2/s5/zpd-log/check.py | 49D1395CFD8FF17D | 7237 |
| build/agent2/s5/zpd-log/setup.py | 594B903C094A5678 | 888 |
| ov/src/graphics/d3d12/command_processor.cpp (a7e79c0 + diff) | DF84086FFD101A4B | - |

Base: rexglue-sdk a7e79c0 `src/graphics/d3d12/command_processor.cpp`. check.txt: blob 00EA93D3, which equals base/ and equals the final2 gpu-leg overlay file (LF-normalised). The diff is add-only and LF, `git apply --check --cached` passes, and ov equals base + diff. I re-hashed ov: DF84086F matches check.txt.

## Verdict

- **Code: SAFE.** With `d3d12_log_occlusion_queries` off (the default), the only differences from HEAD are plain uint64 increments and one `steady_clock::now()` per ZPD packet. There is no change to query, draw or submission semantics and no new log output.
- **Test bin (nops + sync-log + zpd-log, 2 gpu TUs): SAFE-IF Z1-Z5.**

## What I checked

- **OFF behaviour.**
  - Every added line is a counter increment, a const-char* assignment, a scope object, or a log call. The log call returns at once when the cvar is off.
  - No early return, branch or call order of the ZPD handler, IssueDraw, EndSubmission or ShutdownContext changes.
  - The cvar is a plain bool read with REXCVAR_GET (it can change at runtime, which is harmless).
- **Cost.**
  - IssueDraw: one `active_occlusion_query_.valid` test plus an increment per draw, and one more on the skip path only.
  - ZPD handler: a stack scope object, plus one `steady_clock::now()` in the destructor unless it is the first packet or a disable happened. ZPD packets are a few per frame at most, so this is negligible.
  - Logging is at most one line per 10 s while ZPDs arrive, plus first/disabled/shutdown.
- **Races.**
  - The counters are file-scope non-atomics. They are touched only by the ZPD handler, IssueDraw, EndSubmission and ShutdownContext, all of which run on the GPU commands thread.
  - nops-async (6487C0EB) moves only CreateD3D12Pipeline to workers, which never touch these counters. sync-log is in pipeline_cache.cpp.
  - There is one command processor per process, as for the existing skip-list statics.
- **Compiles statically (reading).**
  - `std::chrono::steady_clock` is already used in this TU (base L3572, ov L322).
  - `pixel_shader` is declared at ov L2712, before the skip block.
  - `frame_current_` is a member.
  - `++(c ? a : b)` on two uint64 lvalues is valid.
- **Counter meaning.**
  - The skip path counts `dropped_in_query_no_ps` exactly when `pixel_shader == nullptr`, the same variable the nops opt-in tests. That is the S1 metric.
  - DisableHostOcclusionQueries clears `active_occlusion_query_` before its own EndSubmission(false) (ov L5908-5912), so `ended_by_submission` counts only genuine early ends (cp L4377 hunk).
  - The shutdown log runs before ShutdownOcclusionQueryResources.
- **Base.** The final2 overlay file equals the a7e79c0 blob (check.txt). The stacked bin's pipeline_cache.cpp is the stk TU 9B92AAF9 (a7e79c0 + sync-log + nops) already rated in 6487C0EB / 6968138A. No cvar name collides (`d3d12_async_depth_only_pipelines`, the sync-log cvar, `d3d12_log_occlusion_queries`).

## Conditions (test bin)

- **Z1.** After the freeze, `check.py --compile` must pass (fsyntax + -c with the final2 gpu-leg command), and the stacked pipeline_cache.cpp must be compiled the same way. Record both obj shas.
- **Z2.** Build into a new bin dir with its own MANIFEST and verify-bins PASS, built only from the final2 gpu-leg plus these two TUs (ov DF84086F, stk 9B92AAF9). No pinned or shipped bin is touched. Report the exe sha and a TU list with shas.
- **Z3.** The bin is for diagnostics and functional smoke only. Its timings must not be compared with devfinal2 or native bins, since it differs in 2 TUs and the opt-in arm changes draws.
- **Z4.** Turn the log on per run (`-Cvar d3d12_log_occlusion_queries=true`). Arms: opt-in off and opt-in on (`d3d12_async_depth_only_pipelines=true`), same route. Each run must show a `first` line and a `shutdown` line. With no `first` line, the route issued no ZPD and the arm proves nothing about S1.
- **Z5.** Read-out rules:
  - `dropped_in_query_no_ps > 0` in the opt-in arm confirms S1 for that route, so the opt-in stays off.
  - A 0 counts only if `begun > 0`, `resolved > 0` and host queries were not disabled early (`disabled == 0`, or the `disabled` line comes late with most ZPDs before it). After a disable, every ZPD gets the fake count and drops can no longer under-count.
  - A 0 is route-specific (a lower bound); menus are where ZPD is proven (README).

## Findings

- **S1 (SHOULD).** `disabled` misses one disable path: BeginGuestOcclusionQuery's "begin while another query is active" (ov L5925-5928) calls DisableHostOcclusionQueries directly. A same-address begin while active, which the handler's address check lets through, disables host queries without `disabled++`, without a reason and without the `disabled` log line. It still shows as `fallback` and as later `zpd_no_host` growth, so Z5's "disabled early?" check should also look at `zpd_no_host`. Optional fix: count in DisableHostOcclusionQueries itself, with the reason passed in.
- **N1 (NIT).** `zpd_no_host` counts both cvar-off and resources-unavailable without telling them apart. That is fine for S1, because `occlusion_query_enable` defaults true.
- **N2 (NIT).** The `steady_clock::now()` in the scope destructor could be skipped when the cvar is off (one more REXCVAR_GET). It is negligible either way.
- **N3 (NIT).** The periodic line fires only on a ZPD packet, so a long stretch without ZPDs produces no line until the next packet or shutdown. That is fine for the read-out.
