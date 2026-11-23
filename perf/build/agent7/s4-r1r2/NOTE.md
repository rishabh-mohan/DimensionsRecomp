# S4 #18 (R1 stage 1) + #20 step 1 (R2 counters): staging only (Agent 7, task #9)

Not applied, not built, not run. The live SDK is untouched (its four files hash to `orig/`, checked by
`write_hashes.py` and by the syntax script). Base: SDK `c5fe668e76853630ffc6df2761e9cd8ed5368476`, game `08933a7`.
Ratings it follows: b2r §17 (`perf-notes/agent10-batch2-review.md` L767-807) and its addendum 2 (L1346-1351).

**Agent 10 rated it SAFE** (b2r row 32, §31; no UNSAFE):
- R1 at the default costs one compare per draw and per successful resolve. ON is safe to test with the test plan below.
- R2 step 1 with the macro off is today's `Execute`.
- Before landing it needs the syntax PASS below and a full SDK rebuild, because cp.h's layout changes. It commutes with p2c.

Agent 1: it goes into S4b, a full SDK rebuild, after W4b. Agent 10's one nit is fixed: a dcl.cpp comment put the native
Reset in BeginSubmission, but it is in EndSubmission. Only comment lines changed; see "Syntax check".

## Files

| file | what |
|---|---|
| `r1-split.diff` | #18: `command_processor.h`, `command_processor.cpp`, `deferred_command_list.h` |
| `r2-counters.diff` | #20 step 1: `deferred_command_list.cpp` only |
| `s4-r1r2.diff` | both (the two diffs touch different files, so either one applies alone too) |
| `orig/sdk/...`, `new/sdk/...` | scratch copies: base and staged files, SDK-relative paths |
| `make_new.py` | rebuilds `new/` from `orig/` (exact-once edits; writes nothing if a target is not found exactly once) and writes the 3 diffs |
| `write_hashes.py` | writes `HASHES.txt` (orig/new/diff SHA-256, bytes, lines) and checks live = orig |
| `HASHES.txt` | the hashes; rerun `make_new.py` then `write_hashes.py` after any change |
| `syntax-<stamp>.txt`, `syntax-<stamp>-only.txt` | the reports of `bench/agent7/s4r1r2_syntax.ps1` (all units; `-Only deferred_command_list`) |
| `check_comment_only.py` | proves that a re-staged file differs from the copy the syntax check compiled only in whole-line `//` comments, with the same line count |
| `pre-nit/` | dcl.cpp, HASHES.txt and the diffs from before Agent 10's comment nit was fixed (the dcl.cpp that `syntax-20261122-132724.txt` compiled) |

Diff paths are `a/`, `b/` + SDK-relative. `git -C DimensionsRecomp\rexglue-sdk apply --check --verbose <diff>` exits 0 for
all three (numstat: cp.h +19/-0, dcl.h +3/-0, cp.cpp +87/-4, dcl.cpp +404/-0). Apply (Agent 2 only, after the user
OKs S4): `git -C DimensionsRecomp\rexglue-sdk apply <abs path>\s4-r1r2.diff`.

## Switches (both default off)

| switch | kind | default | effect |
|---|---|---|---|
| `d3d12_submit_split_kb` | cvar, GPU/D3D12, uint32, **kInitOnly** | 0 = off | > 0: after a draw or resolve, end the open submission (not the frame) once its deferred command list holds >= N KB |
| `REX_D3D12_DEFERRED_COUNTERS` | compile macro, `deferred_command_list.cpp` only | 0 = compiled out | 1: per-command-type counts and repeat counts, logged about every 10 s |

- The cvar is read once in `SetupContext` and cached in `submit_split_bytes_`. With 0, each draw and resolve pays one
  compare, and nothing else runs: no log line, no counter.
- Set it at launch (command line or config). Changing it at runtime does nothing until the next start.
- Native builds: leave it at 0 (S17 cond 5).
- The macro is set by adding `-DREX_D3D12_DEFERRED_COUNTERS=1` to that one TU. It changes no header, class layout or
  other file, and OFF compiles to today's `Execute`.

## What changed

### #18, R1 stage 1 (`new/sdk/src/graphics/d3d12/command_processor.cpp`)

- L102-112: the cvar, `.lifecycle(rex::cvar::Lifecycle::kInitOnly)`.
- L1189-1197 (`SetupContext`, after `bindless_resources_used_`): caches the size in bytes, resets the stats and the
  log clock, and logs one INFO line only when on.
- L3107-3111: `IssueDraw` tail, just before the final `return true`. The draw, its barriers and any memexport readback
  are fully recorded.
- L3692-3719: `IssueCopy` keeps the resolve result in `bool resolved` (same calls, same order, same return value) and
  calls the split only after a successful resolve.
- L4364-4409: `MaybeSplitSubmission()`:
  1. It returns at once unless the submission and the frame are open and `deferred_command_list_.GetSizeBytes()` is
     >= the cached size.
  2. A split is due. It holds the split, and tries again after the next draw or resolve, while:
     - an occlusion query is active (EndSubmission would end it early) → `held_query`;
     - the scratch buffer is in use (EndSubmission asserts it is free) → `held_scratch`;
     - pipelines are still being created (`!CanEndSubmissionImmediately()`; EndSubmission would wait for them) →
       `held_pipelines`.
  3. Otherwise it calls `EndSubmission(false)`. True → `splits`. False (no command allocator; the submission stays
     open) → `failed`, and it carries on recording into the open submission. It never calls `BeginSubmission`.
  4. It writes a counter line about every 10 s, only while splits are due and only when on.
- `new/sdk/include/rex/graphics/d3d12/command_processor.h`: L17 `#include <chrono>`; L351-355 the declaration after
  `CanEndSubmissionImmediately()`; L861-872 the members at the class end (`submit_split_bytes_`,
  `submit_split_stats_`, `submit_split_last_log_`). The class layout changes, so every SDK TU that includes the header
  rebuilds. The game (rexlego) includes neither header, so it only relinks.
- `new/sdk/include/rex/graphics/d3d12/deferred_command_list.h` L39:
  `size_t GetSizeBytes() const { return command_stream_.size() * sizeof(uintmax_t); }`.

### #20 step 1, R2 counters (`new/sdk/src/graphics/d3d12/deferred_command_list.cpp`)

- L19-35: the macro, default 0. `<chrono>`, `<cstring>` and `<rex/logging.h>` are included only when it is 1.
- L43-87: `kDeferredCommandNames`, in enum order. L237 has a `static_assert` that it names all 41 commands.
- L89-103: the counters (total and repeat per type, barrier entries, lists, bytes). They are file-static and touched
  only by `Execute`, which runs only inside `EndSubmission` on the GPU Commands thread.
- L105-213: `DeferredCommandShadow`, the state the replayed commands have set on the native list:
  - graphics and compute root state are kept separate: the signature, plus 16 root parameters (constants with a
    per-value valid mask, or CBV/SRV/UAV/table values);
  - descriptor heaps, topology, the index buffer, the last `IASetVertexBuffers` call, RTs + DSV, viewport, scissor,
    blend factor and stencil ref.
- L240: `Execute` builds one shadow, empty, per call.
- L244-415: `count_command` runs before each command is replayed. Every command reaches the native list unchanged and
  in order; the counters only count.
- L659-681: the log, about every 10 s. One `deferred_counters:` header line (seconds, lists, KB, barriers), then one
  line per type with non-zero counts (`total`, `repeat`, %). Then the counts start over.

## S17 conditions

| cond | how it is met | where |
|---|---|---|
| 1: GPU Commands only; tail of IssueDraw/IssueCopy after full recording; never mid-packet, never in swap or RefreshGuestOutput | two call sites only, both at the tail. Xenos has no guest dispatch path | cp.cpp L3107-3111, L3713-3717 |
| 2: guard | cvar > 0 (call sites), `submission_open_`, `frame_open_`, size >= N, no active occlusion query, no scratch buffer, `CanEndSubmissionImmediately()` | cp.cpp L4369-4384 |
| 3: on failure stay open, no BeginSubmission | `failed` branch only counts | cp.cpp L4391-4395 |
| 4: kInitOnly, cached in a member; OFF = today's code | cvar lifecycle; `submit_split_bytes_`; with 0 only the `if` runs, and IssueCopy returns the same value | cp.cpp L109-112, L1191 |
| 5: native builds OFF | default 0; nothing sets it | - |
| 6: no win alone; a test bed | said in the cvar comment and here; it adds a Close + ExecuteCommandLists per split | cp.cpp L102-108 |

R2 step 2 conditions, as far as step 1 already applies them (the counters model the step 2 filter, so the repeat
counts are what it could drop):

| cond | how | where |
|---|---|---|
| (a) pure state setters only | only state setters can count as repeats. Barriers are counted as entries and never compared. Draws, dispatches, clears, copies, queries, resolves, sample positions and markers are counted only | dcl.cpp L321-324, L403-406 |
| (b) resets | new shadow per `Execute` (= per native-list Reset); every root signature set resets all root arguments, a redundant one too; every `SetDescriptorHeaps` resets the tables; graphics and compute are separate; a PSO change resets nothing; a PSO repeats only if it is non-null and equal to the one `Execute` would still draw with | dcl.cpp L133-143, L178-184, L187-188, L381-402 |
| (c) full payload | the whole VB call (start, count, views); the RT array, count, range flag and DSV; the whole IB view (two nulls repeat); viewport, scissor and blend factor by memcmp; constants value by value at their offsets; root values with their kind | dcl.cpp L252-380 |
| (d) a command outside the stream, or an R1 split, resets | `command_list_` is private and has no getter. Outside `Execute`, only SetupContext (Close and QueryInterface, at init) and EndSubmission (Reset just before `Execute`, Close after it) touch it. A split is an `EndSubmission(false)`: that `Execute` ends, and the next EndSubmission resets the native list and runs the next `Execute` from an empty shadow | dcl.cpp L105-112, L240; cp.cpp L4384-4390 |
| (e) debug layer, frame comparison, R1 tests; step 2 only if the counters show enough repeats | test plan (f) below | - |

## Log lines

| line | when |
|---|---|
| `d3d12_submit_split_kb: splitting submissions at N KB of deferred commands` | once at init, only when the cvar is > 0 |
| `d3d12_submit_split: frame= submission= splits= failed= held_query= held_scratch= held_pipelines=` | about every 10 s while splits are due, only when on. Submissions per frame = Δsubmission / Δframe between two lines |
| `deferred_counters: ...` | about every 10 s, only in a `REX_D3D12_DEFERRED_COUNTERS=1` build |

## Syntax check

`bench/agent7/s4r1r2_syntax.ps1`, run at BelowNormal and one compile at a time. It runs clang `-fsyntax-only` with
the dev SDK's exact flags (from `env\compile-one.ps1 -PrintOnly`):

- control: orig copies with the live headers;
- candidate: new copies with `new/sdk/include` first;
- units: cp.cpp; dcl.cpp; dcl.cpp with `-DREX_D3D12_DEFERRED_COUNTERS=1`; and the 6 other SDK TUs that include the
  two headers (graphics_system, pipeline_cache, primitive_processor, render_target_cache, shared_memory,
  texture_cache).

Result: **PASS**.

- `syntax-20261122-132724.txt` (13:27-14:01) covers all 9 units in 18 compiles. Every compile exits 0, and no candidate
  has a new diagnostic: control and candidate have the same 12-20 base warnings per TU. It compiled dcl.cpp
  `183FF8FD...`, from before Agent 10's comment nit was fixed.
- The nit fix changed three comment lines in dcl.cpp, which is now `30FF5744...`. cp.cpp, cp.h, dcl.h and
  r1-split.diff are byte-identical. `check_comment_only.py pre-nit/deferred_command_list.cpp
  new/sdk/src/graphics/d3d12/deferred_command_list.cpp` gives COMMENT-ONLY: 6 changed lines, all whole-line `//`
  comments, and the same line count.
- `syntax-20261122-140147-only.txt` (14:01-14:03, `-Only deferred_command_list`) re-ran both dcl.cpp units on the final
  file `30FF5744...`, with and without `-DREX_D3D12_DEFERRED_COUNTERS=1`. All 4 compiles exit 0, with no new
  diagnostics.

## Test plan (Agent 2 builds, after the user OKs S4; functional runs first, timing last)

1. **OFF = today.** Build with the diff, cvar 0, macro 0. The frames and the log match a base run (logdiff clean), and
   no `d3d12_submit_split` line appears.
2. **Counters build** (macro 1, cvar 0), functional. Read the `deferred_counters` lines:
   - KB per list (KB / lists) sets the split size for step 3;
   - the repeat share per type is the step 2 go/no-go (S17: only if the repeats are big enough for the −0.1 to
     −0.2 ms/frame ceiling).
3. **ON/OFF functional pair** (cvar e.g. half the median KB per list from step 2, plus one stress pass at 16 KB):
   - frame comparison against OFF;
   - logdiff clean apart from the split lines;
   - submissions per frame from the counter line;
   - `failed` stays 0.
4. **D3D12 debug layer** ON vs OFF: no new messages.
5. **Hold paths:** an occlusion-query scene gives `held_query` > 0, and a cold pipeline cache gives
   `held_pipelines` > 0, each with clean frames. `held_scratch` is expected at 0 at the tails.
6. **One pass with `d3d12_readback_memexport=true`** with the cvar on: frames and log clean.
7. **R1 + counters together** (both on), functional. Splits show up as more `lists` in `deferred_counters`, and the
   repeat counts stay sane: each split starts a fresh shadow, so the share can only fall.
8. **Timing** (window 4 / W7 rules) only after 1-7 pass. No win is expected from R1 alone (cond 6).
