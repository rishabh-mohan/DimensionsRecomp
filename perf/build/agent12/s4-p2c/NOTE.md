# S4 P2 memexport full-buffer counter (s4-p2c)

Agent 12, run-2 task #13 step 3. Staged 13:19:33, syntax check PASS at 13:33. Not applied, not built.
**For the next build, not S4a.**

**Agent 10 (b2r row 31, §30, received 13:41): SAFE.** It is output-identical, so it may ship without a switch.
Agent 10's re-apply matches new/ (474C1CBA…), and both apply orders with Agent 7's s4-r1r2 give the same
file (027204B5…). Before P2 is turned ON, someone reads `total` from a next-build run with
`slow_frame_log_ms` set: 0 closes the §22 caveat, and anything above 0 goes to Agent 1.

## Why

- b2r §22 item 4: with P2 on (`shared_memory_single_hold_rearm=true`), IssueDraw's memexport fallback
  `RangeWrittenByGpu(0, SharedMemory::kBufferSize)` would make one long G hold over all of shared memory.
- §25 addendum (Agent 1, ~08:25): P2 ON needs a counter first. The one-TU variant was chosen over the
  frame_stats.h route (5 TUs).
- **No hold cap is staged.** A cap is decided (Agent 1) only if the counter shows the path runs (total > 0).

## What

One file: SDK `src/graphics/d3d12/command_processor.cpp`, +12/-2 in 5 hunks.

1. Anonymous namespace, after `FrameStats()` (new L238-242): `std::atomic<uint64_t> memexport_full_buffer_draws{0};`
   plus a 3-line comment.
2. `ReportSlowFrame` (runs on every swap, command thread), after the frame_stats snapshot loop and before the
   threshold's early return (new L264-266): exchange the count to 0 and add it to a function-static total.
3. The slow-frame line ends in ` | memexport full-buffer {}x (total {})` (new L283-284, args new L293).
   Placeholders and args both go from 23 to 25.
4. IssueDraw's else branch (new L3073): `fetch_add(1, relaxed)` right after the full-buffer `RangeWrittenByGpu`.

No header, no cvar, no new include (`<atomic>` is already included at L15).

## Behaviour

- **Output-identical unless `slow_frame_log_ms` is set.** The count appears only in the slow-frame line.
- `Nx` is the number of full-buffer fallback draws in that frame. `total` counts since process start, including
  frames that were not logged, because the snapshot runs on every swap, before the threshold check.
- It doesn't depend on P2's cvar. It counts the path with P2 on or off, so any next-build run with
  `slow_frame_log_ms` set already shows whether the path runs.
- Cost: one relaxed `fetch_add` per fallback draw, and one `exchange` plus one add per swap. Both sites run on
  the command thread: IssueDraw, and IssueSwap calling ReportSlowFrame.
- Not counted: Vulkan's full-buffer call (`vulkan/command_processor.cpp:4166`; that backend is unused). Resolves
  (`texture/cache.cpp:349`) are ranged, not full-buffer.

## Parsers and logdiff

- `bench/agent5/s4_slowframe.py` uses an un-anchored search, and `bench/agent12/s4_uhash.py`'s SLOW regex needs
  only `slow frame #N: X ms |`. Both tolerate the extra field.
- Regex for the field: `memexport full-buffer (\d+)x \(total (\d+)\)`.
- Logdiff caveat: across builds, with `slow_frame_log_ms` set, every slow-frame line's text changes because of
  the new field. Compare fields, not raw lines. Default runs (cvar unset) are unaffected.

## Overlap and apply order

- No overlap with #7 (s4-diag, `d3d12/shared_memory.cpp`), #8 (s4-p2, `shared_memory.cpp`) or #5 (s4-fixi,
  `xmemory.cpp`): they touch different files. A joint `git apply --check` of #7 + #8 + #5 + this diff on the
  live SDK passes.
- None of S4a's other items touch this file: #38 `core/timer_queue.cpp`, #32 `d3d12/pipeline_cache.cpp`,
  #2 rexlego `gpu_native/shaders.cpp`. Neither do Agent 2's S3/S3d/S3e/RB/B diffs. So the base is the live
  file, 3AB3AA53… (= the S4a output for this file).
- #18 (Agent 7's R1 stage 1, RefreshGuestOutput submit split), #19, #33 (optional part) and #34 (~:2727) edit
  the same file. This diff's hunks, on the live file: L235-240, L256-261, L272-278, L280-286, L3061-3066. The
  edits are inserts after L237, L258 and L3063, and changes to L275 and L283. Agent 7's s4-r1r2 commutes with
  this diff: Agent 10 applied it in both orders and got the same file, 027204B5…. For any later change to this
  file, check both apply orders again. make_p2c.py's anchors are content-based, so a rebase only needs a
  BASE_SHA change and a re-run.

## Agent 10 checklist

- Placeholders and args are both 25. fmt's compile-time format check passes, as the syntax check shows.
- The atomic is constant-initialized (namespace scope, `{0}`): no init-order issue.
- Both sites run on the command thread. Relaxed ordering is enough: the `exchange` in ReportSlowFrame is the
  only reader, and nothing else is ordered by it.
- `full_buffer_total` is a function-static `uint64_t` touched only by ReportSlowFrame (command thread).
- With `slow_frame_log_ms` unset, the counter is the only change.

## Test plan (next build)

- P2 ON: `-Cvar 'shared_memory_single_hold_rearm=true;slow_frame_log_ms=1'`, then a title + menu walk (+ a level
  load when allowed). Read `total` on the last slow-frame line.
  - total = 0: P2 ON's memexport gate closes, because the fallback never ran.
  - total > 0: Agent 1 decides the hold cap, or whether P2 stays off.
- A P2-OFF run with `slow_frame_log_ms` set (for example a u-diag run on the next build) answers the same
  question.

## Checks

- `make_p2c.py` RESULT PASS (13:19:33):
  - every anchor matched exactly once; LF only;
  - 12 added lines, longest 98 columns, no trailing space;
  - the diff touches only this file;
  - `git apply --check` on the live SDK passes;
  - a scratch apply in %TEMP% reproduces new/ byte for byte;
  - the joint check with #7 + #8 + #5 passes.
- Syntax check (`bench/agent12/s4p2c_syntax.ps1`; BelowNormal, 1 thread, no PCH, no objects):
  `syntax-20261122-132026.txt`, **RESULT: PASS**.
  - pristine: exit 0, 419.0 s (loaded machine), 20 diagnostics;
  - candidate: exit 0, 44.4 s, 20 diagnostics, sha = HASHES staged;
  - no new diagnostics. All 20 are existing SDK-header warnings (-Wunused-parameter, -Wnontrivial-memcall).

## Files

| File | SHA-256 |
|---|---|
| `orig/command_processor.cpp` (= live) | 3AB3AA5360D4E9875DCA8550346EE368EC9188BDC454C2EB93D9BB915BD1AD97 |
| `new/command_processor.cpp` | 474C1CBAE6359D9EB9FD313FF541EEA2CF6A6987A5BCAE1821EFDF75A6B86EFF |
| `memexport-full-buffer-counter.diff` (2998 B) | 29E02E249EDDFEFD702CFBF6D7A36B6A3D060E9DFC9A8FD6F621BB0FE151BDE2 |
| `syntax-20261122-132026.txt` (10786 B) | C19778A97370F70E007A18A84882CD358B840F926AA583AF4D8D5EAA0AEF3EA2 |
| `make_p2c.py` | D3DECDA359C0C3DCF413986BC2F3F7A0AB76FD2EB1C3B1E0BBA32C78804D0518 |

Apply (next build only), from the SDK root `DimensionsRecomp/rexglue-sdk`:
`git apply ../../build/agent12/s4-p2c/memexport-full-buffer-counter.diff`.
