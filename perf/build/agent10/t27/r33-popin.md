# #33 rating: no-wait pipeline creation (the pop-in opt-in)

Agent 10, task #27 (an optional rating; Agent 1 asked for it). Read-only work on 2026-11-23, 07:24-07:36: nothing was applied, built or run.

**Files rated** (`build/agent6/s33-popin/`, unchanged since 06:47):

| file | sha256 (first 16) | lines |
|---|---|---|
| `s33-popin.patch` | 0D23024484CCDEE1 | 220 |
| `DESIGN.md` | 611B62F510948253 | 264 |
| `CHECK.txt` | 43A4F21167FE5823 | 89 |

**Base.** `DimensionsRecomp/rexglue-sdk` HEAD is 5350b1de99276b7a7be701bf00914f1ee58ce9bc. For all 4 target files, `git hash-object` on the worktree file equals `git rev-parse HEAD:<path>`:
- `include/rex/graphics/d3d12/pipeline_cache.h`: 7e81db3b1402, 435 lines
- `src/graphics/d3d12/command_processor.cpp`: 6f21eb6f220a, 5933 lines
- `src/graphics/d3d12/pipeline_cache.cpp`: 55e9f02ef54b, 3335 lines
- `src/graphics/frame_stats.h`: 8c169b418cb5, 72 lines

`git apply --check --verbose` at 07:24 printed the 4 "Checking patch" lines and exited 0, with no offsets. The only SDK worktree change is the `thirdparty/simde` submodule entry.

Line numbers are those at 5350b1d, except where it says "patch L".

## Verdict

- **OFF (the default): SAFE.** Control flow is the same as at 5350b1d. Behaviour doesn't change; there are three small differences:
  1. The slow-frame line gets 3 more fields at the end (patch L37-38, L47-48). The line prints only when `slow_frame_log_ms` > 0, and its default is 0 (command_processor.cpp L79, L285).
  2. Each dropped draw adds one counter: `frame_stats::Add`, which is two relaxed `fetch_add`s (frame_stats.h L47-52).
  3. `ReportSlowFrame` resets 2 more counter slots per swap (the loop to `kCount`, L269-275).
- **ON (cvar true), as an opt-in test: SAFE-IF**, under these conditions:
  1. The default stays false, with `kRequiresRestart` (patch L109-114). This is already how it's staged.
  2. Row 1 (cvar off, patched bin against the base bin) shows identity before anyone reads ON timings (DESIGN §8 L233, §9 L257).
  3. The user's row-3 review on a visible desktop gates any recommendation (§8 L235, §9 L259).
  4. The first test bin leaves out hunk #5 (S1 below).
- No BLOCKER. 2 SHOULD and 4 NIT.

## What I checked

### OFF is the same code path (DESIGN §3 L92-102)

- **#4, IssueDraw** (patch L56-78 against L2757-2760). The new condition is `(async || IsCreationNoWait()) && state == null`.
  - With async on (the default, `src/graphics/command_processor.cpp` L126), `IsCreationNoWait()` isn't evaluated.
  - With async off it returns false, so the condition is the old one.
  - Inside the branch `skip_draw` stays true and the guard at patch L65 is false. The code counts, then returns true, as L2759 did.
- **#9, EndSubmission** (patch L178-207 against pipeline_cache.cpp L795-814).
  - Patch L189-206 are old L796-813 line for line, one indent level less.
  - The early return when `creation_threads_` is empty replaces the old `if (!creation_threads_.empty()) {...}`.
  - Hunk counts: old 3 + 19 + 3 = 25 and new 3 + 28 + 3 = 34, which matches the hunk header (`-792,25 +829,34`). The braces balance.
- **#5** (patch L85-91): `!open || false || !creating`, the same as before.
- **#8** (patch L145-151): the new block is skipped.
- **#7** (patch L126-137): the cvar test comes first in the `&&`. With the cvar false, nothing else is read and nothing is logged.
- **#10** (two new ids): only `ReportSlowFrame` walks the counters (L269-275). I grepped SDK `src/` and `include/` for `frame_stats::kCount`, `Counters()` and `frame_stats::Id`, and found no other user. texture_cache.cpp, shared_memory.cpp, pipeline_cache.cpp and `src/graphics/command_processor.cpp` include the header only for `Add` and `Scope`.
- **#3, the slow-frame line:** L291-304 have 25 placeholders and 25 arguments. The patch adds 3 of each, giving 28/28. The new `{:.1f}` gets `ms(...)`, a double; the two `{}` get uint64 counts. This agrees with CHECK L76.

### Log parsers (the one change visible with OFF)

I searched 364 .py/.ps1/.psm1 files under `build/agent3`, `6`, `7`, `9`, `11`, `12`, `bench/agent5`, `bench/agent8` and `harness/` (depth 3) for "full-buffer", "slow frame #" and "(total". None anchors the slow-frame line at its end:
- `bench/agent5/s4_slowframe.py`: the regex at L41-45 stops at "(on memexport pages ...)".
- `build/agent12/p2c-check/p2c_check.py`:
  - L81-82 aren't anchored, on purpose (comment at L79-80).
  - The L92 LITERAL is still a byte substring of the patched string, because adjacent literals are joined: "...(total {}) | dropped draws ...".
- `build/agent3/f10/f10_results.py`: L31 takes the rest of the line with `(.*)$`, and the field regexes at L32-36 aren't anchored.
- `build/agent3/f10/sync_profile.py`: L8 stops at "memexport syncs (\d+)".
- `build/agent6/attract-stalls/slowframe_join.py`: L29-35 stop at "stalled".
- `build/agent6/w6/log_diff.py` L59 and `build/agent3/s4b/s4b_check.py` L30 aren't anchored.

### ON

- **The invariant: no draw is recorded with a null pipeline.**
  - IssueDraw is the only code that records pipeline handles (L2780). Grepping `SetPipelineStateHandle` in `d3d12/` finds no other recorder; L1051 is a direct `D3DSetPipelineState`.
  - The replay resolves the handle at Execute (deferred_command_list.cpp L620-626). When it's null, the replay skips `SetPipelineState` without a message. A pending draw recorded there would therefore draw with the previous PSO.
  - With the latch set, the drop check runs before L2780 for every draw, even if async is turned off later (patch L61).
  - `state` is written once, from null to its final value, with a release store (pipeline_cache.cpp L1071, L3270, L3272, L3301, L3305). It's read with an acquire load (pipeline_cache.h L101-103).
  - So a draw that passes the check is still valid at replay without the EndSubmission wait. **OK.**
- **Only async pipelines can be pending.** Those are queued only when `use_async` holds: async on, creation threads present, and a pixel shader (pipeline_cache.cpp L942-943, queued at L1051-1068). Everything else is created synchronously (L1070-1071). **OK** (matches DESIGN §7 L183).
- **The forced wait** (patch L65-74).
  - After `AwaitPipelineCreation`, the queue is empty and `creation_threads_busy_` is 0.
  - That holds because the pop and `++busy` happen under one lock (L3263-3265), and so does `--busy`, after the store (L3280-3281).
  - So the re-check sees the final state: created, or null if creation failed, in which case the draw is dropped and counted.
  - `memexport_used` is in scope (L2684). `active_occlusion_query_.valid` is set at L5840 and cleared at L4279, L5728, L5804, L5811 and L5852. **OK.**
  - ON is stricter than OFF for these draws. With OFF, a memexport or in-query draw whose pipeline is pending is dropped for the rest of its submission: L2757-2759 run before any memexport handling. With ON it waits (§7 L181-182).
- **Root signature.**
  - IssueDraw uses the root signature that `ConfigurePipeline` returned (L1038, L1089), which it took before the forced wait.
  - With bindless the signature is fixed, so the latch's bindless term (patch L126-128) is what makes the forced wait safe.
  - With bindful resources the worker replaces it (L3226-3233; DESIGN R6 L214-219). **OK.**
- **One waiter at a time.**
  - `creation_completion_event_` and `creation_completion_set_event_` form a handshake for a single waiter (L149-151, L805-807, L3248-3251).
  - After the patch, `AwaitPipelineCreation` is called from:
    - IssueDraw and EndSubmission, on the GPU thread;
    - `ShutdownShaderStorage` from `Shutdown` (L189). The threads are joined and cleared at L175-185 first, so the early return fires before anything touches the event that L186 resets;
    - `ShutdownShaderStorage` from `InitializeShaderStorage` (L224). That runs on the GPU thread through `CallInThread` (graphics_system.cpp L385-388, L392-394), or on the caller's thread only while the CP is paused (L379-382). **OK.**
- **#8, the storage close.**
  - With ON, workers may still be translating and queueing storage writes when `InitializeShaderStorage` → `ShutdownShaderStorage` clears the queues and closes the files (L761-777).
  - #8 drains and waits first. **OK.**
  - With OFF the narrow race remains; it predates this patch (DESIGN L89).
- **Shutdown.**
  - Workers finish the pipeline they hold and exit (`creation_threads_shutdown_from_ = 0` at L178; the exit is at L3247 and L3253-3254).
  - Queued pipelines that never started keep a null state and are deleted with the rest (L193-199). No recorded draw refers to them.
  - Exit takes at most one pipeline compile per worker. Row 4 tests this. **OK.**
- **Hunk #5** has two callers:
  - `OnPrimaryBufferEnd` (L2587-2591), through `d3d12_submit_on_primary_buffer_end`, default true (L98);
  - `MaybeSplitSubmission` (L4392), only with `d3d12_submit_split_kb` > 0; the default is 0 (L109).
  - See S1.

## Findings

**S1 SHOULD: build the first test bin without hunk #5** (patch L82-93, the whole hunk: its header, 7 context lines, 1 removed and 4 added lines).
- With #5, ON also changes where submissions end during bursts:
  - `OnPrimaryBufferEnd` (L2587-2591; the cvar is on by default, L98) ends a submission at every primary-buffer end while pipelines are being created. OFF never does that, because `CanEndSubmissionImmediately()` is false while `IsCreatingPipelines()`.
  - The result is more, smaller submissions.
  - During bursts, it also ends early a guest occlusion query that spans a primary-buffer end (L4276-4280; DESIGN R4 L207-210).
- That puts a second variable into row 2's timing and into the user's row-3 review.
- Without #5, ON differs from OFF only in the EndSubmission wait and the IssueDraw guard. `CanEndSubmissionImmediately()` stays false during bursts, as with OFF.
- DESIGN L210 and CHECK L40-42 already say #5 can be deleted on its own.
- Suggestion: stage a copy of the patch without hunk #5, apply-checked on 5350b1d, for the first bin. #5 can become its own arm once row 2 is in.

**S2 SHOULD: run the resolve-after-drop diagnostic (d) before any recommendation** (DESIGN L193, §9 L256-264).
- EDRAM resolve sources aren't guarded (§7 L185).
- ON widens the loss from one submission to the whole creation window. A pass that runs only once (a capture, a portrait, a menu background) then stays wrong until the game draws it again.
- Today the row-3 review is the only guard, and it can miss a one-off capture that isn't on screen at the time.
- §9 lists (d) only as a follow-up (L263). Add it as a 5th precondition to §9 L256-260 before #33 is suggested to anyone as a setting.
- It isn't needed for the opt-in test bin.

**N1 NIT: the header comment for the now-public `AwaitPipelineCreation()`** (patch L9-12).
- Add the threading rule from DESIGN §4 L133: "GPU thread, or the thread acting for it while the CP is paused; never two callers at once".
- The event and flag pair (L149-151, L3248-3251) supports only one waiter.

**N2 NIT: "forced pipeline waits (Nx)" counts calls, not stalls.**
- The Scope at patch L70 counts every forced call, including cheap ones with nothing pending.
- For example, R2: a failed pipeline on a memexport or query draw makes the call on every such draw.
- Readouts should take the ms, not the count, as the stall measure. Say so in the row-2 notes.

**N3 NIT: allow-lists for the ON and gate arms in Agent 3's s4b kit.**
- DESIGN §8 L247-250 adds expect rules to the w6 kit.
- If an ON or gate arm goes through `build/agent3/s4b/postcheck.ps1` / `s4b_check.py`, the INFO line (patch L130-132) or the WARN line (patch L134-136) is a new log family there too.
- Add `d3d12_pipeline_creation_no_wait` to that row's `--allow-new` for those arms, and keep it unexpected for OFF arms.

**N4 NIT: PENDING-DIFFS is out of date for #33 and #34** (Agent 2's file, 4699E6CB…, 06:34).
- L39 still shows the placeholder `d3d12_async_pipeline_no_wait` and "Design only".
- L40's #34, the dropped-draw counter, is now part of #33 (hunks #3, #4 and #10).
- L65 says "none found"; L130 is also stale.
- When the patch is staged for a bin, update these with the path, sha 0D230244… and the apply check (exit 0 on 5350b1d).

**Not findings:**
- R5: the plain-bool race on `shader_storage_file_flush_needed_` (L3197 against L792) and the unlocked storage reads (L3193-3195) predate this patch. ON widens their window (DESIGN R5 L211-213), and #8 covers the reopen path.
- R8: nothing has been compiled. The names and macros I looked up exist (CHECK L58-68 and the greps above).

## Read / Sent

- **Read (07:24-07:36):**
  - `s33-popin.patch` (all), DESIGN.md L68-264 (L1-67 read earlier), CHECK.txt (all);
  - SDK at 5350b1d:
    - command_processor.cpp L255-305, L2570-2600, L2730-2782, L4255-4410 and L5790-5860;
    - pipeline_cache.cpp L135-230, L670-830, L936-960, L1028-1092 and L3225-3335;
    - pipeline_cache.h L99-104; frame_stats.h (all);
    - deferred_command_list.cpp L396-403 and L614-627;
    - graphics_system.cpp L370-398;
  - the regex lines of the 7 parser files listed above;
  - `build/agent2/PENDING-DIFFS.md` L20, L39-40, L65 and L130;
  - `build/agent6/HANDOFF.md` L32-35 and L87-92;
  - RESUME L110 and L275-277.
- **Sent:** 07:36, to Agents 6 and 1.
- **Adopted (checked 07:44):** Agent 6 recorded this rating, docs only, in `build/agent6/s33-popin/DESIGN.md` §10 (B2E33FE8B99F4041…, 299 lines; §8 now builds without #5, and §9 item 5 is S2) and in `CHECK.txt` (5101A7B136CCCBE4…, 115 lines). The rated patch is unchanged (0D23024484CCDEE1…). §10 matches this file. Its range for hunk #5, L82-93, is right; S1 above said L82-91 until 07:44.
