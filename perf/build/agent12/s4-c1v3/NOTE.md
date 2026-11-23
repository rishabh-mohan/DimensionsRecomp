# S4 C1 v3: C1 v2 + the init latch (s4-c1v3)

Agent 12, run-2 task #13 follow-up. Staged on scratch at 14:22:38 and not applied or built.
- C1 v1 (`build/agent12/s4-c1/`) and C1 v2 (`build/agent12/s4-c1v2/`, rated SAFE in b2r row 35, §34) are
  unchanged. make_c1v3.py re-checks v2's 11 copies and 3 diffs against v2's HASHES.txt and only reads them.
- **The S4b tests use v2.** v3 is the version for Agent 10 to rate before default-ON or any landing beyond tests.
- **Update (2026-11-23, task #24): v3 replaced v2 in S4b, so the line above is out of date.**
  - Agent 10 rated v3 in b2r §35 (14:28-14:45): SAFE at the default; ON is SAFE to test when set at launch.
    Landing is as for v2: a full SDK install and game rebuild, then re-pin the native baselines.
  - Agent 2 composed S4b with `--c1 v3` (`build/agent2/s4b-compose-1932-c1v3.txt`), so devoff4b runs C1 v3.
  - The 5 SDK files in `new/sdk/` are byte-identical to rexglue-sdk perf/opt 5350b1d (`git hash-object
    --no-filters` against `git rev-parse 5350b1d:<path>`, 06:04). The line numbers in this NOTE therefore also hold
    for that commit. Both cvars default to OFF there.

## Why

- Agent 10, §34 (~14:12): v2 is SAFE at the default and ON is SAFE to test. But kInitOnly only takes effect in
  the settings overlay. `FinalizeInit()` has no caller, so the developer console (`console_overlay.cpp:221`,
  `SetFlagByName`, `Source::kRuntime`) can still flip both cvars. Agent 10 wants an init latch before
  default-ON or any landing beyond tests.
- §34 nit 2: on native, V4's exchange runs on every protect. A load first would skip it.

## What

v3 differs from v2 only in SDK `src/system/xmemory.cpp`. No header changes. `v2-to-v3.diff` is +24/-6 in
6 hunks.

- **L0:** one comment line on the cvars says that Memory::Initialize latches both.
- **L1, the latches:** `physical_protect_hold_global_lock_latched` and `physical_protect_keep_watch_latched`.
  Both are file-static `constinit std::atomic<bool>` (default false), at the top of `namespace rex::memory`.
- **L2, latch at init:** Memory::Initialize reads both cvars once into `hold_on` and `keep_on`, then stores
  them in the latches (relaxed). This runs right after `file_name_`, before the arena and before any heap.
  v2's state line (V5) uses the same locals.
- **L3, the runtime reads:** PhysicalHeap::Protect's two cvar reads now load the latches (relaxed):
  - L3a: fix (i)'s hold condition;
  - L3b: C1's gate.

  After v3, the only `REXCVAR_GET`s of either cvar are the two in Memory::Initialize, and no other staged file
  reads or declares either one. make_c1v3.py checks both.
- **N2:** NoteKeepWatchBlocked does a relaxed load before its exchange.
- **Unchanged:**
  - v2's kInitOnly on both cvars, so both stay read-only in the overlay;
  - the counter and its lines (V2, V3);
  - V4's position. Gate C's positive check still fires on native; "blocked" is not folded into the latch;
  - `physical_protect_keep_watch_verify`, which stays kRequiresRestart. Flipping it at runtime produces false K
    lines and also false F lines (corrected 2026-11-23: see "Verify-mode caveats" below).

## Behaviour

- **OFF (the default): the same path and the same log as v2.**
  - Init does two cvar reads and two relaxed stores, where v2 did one read.
  - In Protect, a relaxed atomic load replaces a cvar read. On x64 both are plain loads.
- **ON, set at launch: the same as v2.**
  - Cvars are loaded before Memory::Initialize, which already read `protect_zero` and printed v2's line from
    them.
  - The latches are stored before any heap exists and before any guest thread starts, so every Protect sees
    them.
  - Every mix of the two values is safe anyway. Keep-watch without the hold can't engage (the `owns_lock()`
    gate), and the hold alone is fix (i).
- **A developer-console set after init has no effect on Protect in this process.** The console and overlay
  show the new value, but the latched value is the one that counts. A restart is needed to change it.
- **Native with keep_watch on:** v2 did a locked exchange on every protect after the first line, and v3 does a
  relaxed load. The log output is the same.

## Logging under G (corrects v2's NOTE, §34 nit 1)

v2's NOTE named AccessViolationCallback's two lines (L657, L672) as the precedent for logging under G. As
Agent 10 points out, those run after G has moved into TriggerCallbacks. The real precedents, using v2's
xmemory.cpp line numbers, are:
- `PhysicalHeap::Decommit`: REXSYS_ERROR at :2211, with G acquired at :2207;
- `PhysicalHeap::Release`: REXSYS_ERROR at :2226, with G acquired at :2222.

v2's NOTE stays byte-identical, as rated.

## Apply order and landing

- If v3 replaces v2, apply on top of S4a. This is Agent 10's §34 order with v3's diff:
  1. SDK: `keep-watch-v3.diff`, which replaces `keep-watch-v2.diff` (5 SDK files, S4a output → C1 v3);
  2. game repo: v1's `keep-watch-rexlego.diff`, unchanged (keep CRLF).
- For reference, from the live tree: `chain-live-to-c1v3.diff`.
- Landing needs the same steps as v1 and v2:
  - a full SDK install plus a game rebuild;
  - then re-pinned native baselines (native3d, nativeB).

## Test plan

v2's plan applies unchanged:
- set both cvars at launch;
- ON runs include one level load;
- on native with both on, expect `on, but blocked` and one `blocked` line.

v3 adds no log line. A developer-console flip isn't part of the plan, because by design it has no effect.

## Checks

- **`make_c1v3.py`: RESULT PASS (14:22:38).**
  - v2's 11 copies and 3 diffs, plus v1's rexlego diff, match v2's HASHES.txt, and the 7 live bases match.
  - Each of the 6 anchors matched exactly once. The 23 added or changed lines are at most 92 columns, with no
    trailing space and no tab; LF only.
  - Read sites: 2 `REXCVAR_GET`s, both inside Memory::Initialize. There are 2 latch loads and 2 stores. The
    other 5 staged files have no `REXCVAR_*(name)` or `cvars::name` for either cvar.
  - `git apply --check` exits 0 on the live SDK for diag, P2, fix (i) and `chain-live-to-c1v3.diff`, and on the
    live game repo for `keep-watch-rexlego.diff`.
  - On scratch, outside any work tree:
    - v2's xmemory.cpp + `v2-to-v3.diff` = v3's xmemory.cpp;
    - the 4-step chain #7 → #8 → #5 → `keep-watch-v3.diff` on copies of the live files reproduces every staged
      file.
  - The first run, at 14:21:46, failed only an over-broad check: it counted plain-name hits, which were comments
    and the verify cvar. That run is replaced; its outputs were identical.
- **Syntax check (`bench/agent12/s4c1v3_syntax.ps1`): RESULT PASS.**
  - Report: `syntax-20261122-142307.txt`, 14:23:07-14:23:51.
  - Setup: BelowNormal, 1 thread, no PCH, no objects. The control is v2's xmemory.cpp and the candidate is v3's.
    Both compile with the staged C1 headers first, and those headers equal HASHES `new`.
  - Control: exit 0, 15.6 s, 1 diagnostic. That is the known `unused parameter 'global_lock_locked_once'`
    (:2511).
  - Candidate: exit 0, 14.2 s, the same 1 diagnostic (:2529). Its sha BCA5E1CF… equals HASHES `new`.
  - No new diagnostics.

## Files

| File | SHA-256 |
|---|---|
| `v2/sdk/src/system/xmemory.cpp` (= C1 v2 new, 119,957 B) | DC23757AC206FCC51F03B89C0A77F8EFCDB372B138C5D72600C230C295EC8CFD |
| `new/sdk/src/system/xmemory.cpp` (C1 v3, 121,109 B) | BCA5E1CF63686E73FC5A12642B9B169E155FBBEC65D0A56CE1BE9B0B71022794 |
| `v2-to-v3.diff` (80 lines, 6 hunks, +24/-6) | 1FC8E2DCC452A6EFFA1066FFBED0592D5BA8A74DE5FA322D7E978CFD4D9D1190 |
| `keep-watch-v3.diff` (597 lines, 20 hunks, +422/-5) | DECCFE3373C27C3C8442A26A3C4DDFDB01CE54E2C4912CDE6701484185D66F48 |
| `chain-live-to-c1v3.diff` (829 lines, 25 hunks, +614/-3) | 0E61E1D07C2BAB99B8ED0CBAE948B0035B8721D889501FC267D9D331DDF47817 |
| `keep-watch-rexlego.diff` (v1's, reused) | 4D0C10794188CF450046D42B249C9C46D009EE9F4F1B82116954857FA70838BD |
| `make_c1v3.py` | 3FD56FD020D938423B993AE95CBDCA553753500E5AC2C6270A8B479CAB572CB0 |
| `bench/agent12/s4c1v3_syntax.ps1` | BAACF88DEBDB30A800450DFB5F2D52998C5E91296C6B55DC1A5FA93B4F3DA30F |
| `syntax-20261122-142307.txt` | A82E9C879059AAC354C2649D60D080A50E9B3B984621B589AEB32A3C16FEF078 |
| `HASHES.txt` | 0C5D3304D2D5839A85788A3FE86EC35F19E33D7BA70D0F65B998A565ACE95743 |

The other four `new/sdk` files equal v1's and v2's new copies: xmemory.h 5A70782E…, shared_memory.h 82A66445…,
primitive_processor.cpp 470BA4BE… and shared_memory.cpp A4A31038…. Full hashes are in `HASHES.txt`.

## Verify-mode caveats (2026-11-23)

Added after the night windows, at Agent 1's request (22:55). No code and no hash above changes. This section
corrects and extends what this NOTE says about `physical_protect_keep_watch_verify`. Line numbers are in the
staged `new/sdk/src/graphics/shared_memory.cpp` (= live, A4A31038…).

- **A runtime flip gives false F lines too, not only false K.** This corrects the last "Unchanged" bullet.
  - KeepWatchVerifyRecord runs only while the cvar is on (L381).
  - The F check in MemoryInvalidationCallback runs whenever the page has a stored hash (L581).
  - After a runtime verify-off, the stored hashes stay but are no longer refreshed. A later write fault then
    compares the new data with an old hash.
  - Found by Agent 10 (b2r row 42, §41).
- **Without P2 (`shared_memory_single_hold_rearm`), verify can report false F lines.** This explains row 7's
  F 92 (`20261122-214221-s4b-07-c1v-level`, K 0). Agent 10's subagent B confirmed it.
  - MakeRangeValid (L335-384) sets the valid bits under G (L356-371; the set is at L367) and releases G.
  - It then arms the watch (L373-377).
  - Only after that does it re-hash the pages (KeepWatchVerifyRecord, L381-383 → L684-705).
  - A write fault in that gap runs the F check (L577-583) against the hash from the page's previous upload.
    Invalidation never clears the hashes.
  - With P2, single_hold_lock (L351-354) holds G until L384, so there is no gap. Gate A (p2fc + verify, same
    route and tags) had F 0.
  - Wording fix (Agent 10): the valid bits are also written at L63/L114/L124/L134. Those writes only clear
    them; they are set only at L367.
  - **Until this is confirmed, read F lines from a verify run without P2 as "unverified", not as a C1
    failure.** C1 ships only as p2fc. Either test settles it:
    - **s4bV0:** C1 off, otherwise row 7 (L route + tags, 600 s). Predicted: F > 0 on pages
      01AE8000-022BF000, thread XThread90B8 (F80001A8). F = 0 would refute this explanation.
    - **The verify-only fix:** zero `keep_watch_verify_hashes_[page]` inside the L356-371 G block, re-run
      row 7, and expect F 0.
- **Another false-F cause (Agent 10): XFile::Read.** XFile::Read writes file data through the physical alias
  and invalidates the range only afterwards (SDK `src/system/xfile.cpp` L266-295). A guest write fault on such
  a page before that invalidation finds data that no longer matches the stored hash.
- **After-S4 candidate: verify's per-upload VirtualQuery.** Under verify, the CP (the `GPU Commands` thread)
  is about half kernel-bound.
  - Row 7 and gate A: 91% of the CP's CPU time is kernel time. The median kernel% per 2 s is 49 (row 7) and
    47 (gate A).
  - The 10 non-verify runs: 20-36% kernel, with a median kernel% per 2 s of 4-16. That includes C1-on gate B
    (27% / 11).
  - User time is ~9% of the CP's CPU, so the cost isn't the XXH3 hashing.
  - Suspect (inferred, not profiled): KeepWatchVerifyRecord (L684-705, holds G from L686) →
    KeepWatchVerifyReadable (L668-679) → `memory::QueryProtect`, which is VirtualQuery + RegionSize
    (rexglue-sdk `src/core/memory_win.cpp` L157-171). It runs at least once per MakeRangeValid, because
    readable_end is local (L694).
  - Fix ideas:
    - read the heap's own page-protect state instead of calling VirtualQuery;
    - hash under SEH and skip pages that fault;
    - keep the last query's region across calls.
  - Verify is a test mode, so this doesn't block S4. It does make verify runs slower, and G is held longer
    while it runs, so verify runs are not timing-comparable with non-verify runs.
