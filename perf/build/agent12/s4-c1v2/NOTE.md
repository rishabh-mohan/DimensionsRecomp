# S4 C1 v2: physical_protect_keep_watch + the kept-protect counter (s4-c1v2)

Agent 12, run-2 task #13 step 5. Staged on scratch at 13:49:32 and not applied or built. This is a re-stage with
kInitOnly on both cvars; the first staging, at 13:31:39, had kRequiresRestart on C1's cvar only.
C1 v1 (`build/agent12/s4-c1/`) is unchanged. make_c1v2.py re-checked its 12 copies and 3 diffs against its
HASHES.txt and only reads it.

## Why

- Agent 10, b2r §28 (`perf-notes/agent10-batch2-review.md` L1532-1548, row 29, 13:05-13:15): C1 is SAFE at
  the default. **ON is SAFE to test once gate D has a kept-protect counter (C1 v2).** Without one, a clean log
  can't show that C1 engaged (§24 L1242-1244). The same counter is gate A's positive control.
- Agent 1's C1 v2 list (08:12, my notes RESUME):
  1. Required: a kept-protect counter plus a log line on the first kept protect. It also gives gate C a
     positive check on native.
  2. Optional: a one-time warning when C1 is on without fix (i), and restart-only switches on both cvars.
  3. After the apply: re-pin the native baselines.

## What

v2 differs from v1 only in SDK `src/system/xmemory.cpp`. No header changes. `v1-to-v2.diff` is +43/-3 in
5 hunks; V1 and V6 share the first hunk.

- **V1, init-only switch:** `.lifecycle(rex::cvar::Lifecycle::kInitOnly)` on `physical_protect_keep_watch`,
  plus two comment lines that say why.
- **V6, init-only switch on fix (i)'s cvar:** the same lifecycle on `physical_protect_hold_global_lock`. This
  edits #5's definition inside this diff, on top of #5. #5's staged diff (`s4-fixi/protect-hold-g.diff`
  80CAD795…) is unchanged and stays as rated in §23.
- **V2, counter and helpers:** file-static, after `Memory::IsPhysicalProtectKeepWatchBlocked()`.
  - Two atomics:
    - `physical_protect_kept_count` (`constinit std::atomic<uint64_t>`);
    - `physical_protect_keep_watch_block_logged` (`constinit std::atomic<bool>`).
  - `NoteKeptProtect(address, size)` logs `C1 keep-watch: first kept protect at {:08X}, {} bytes` once. After
    that it logs `C1 keep-watch: {} protects kept so far` at 2, 4, 8, … 2048 and at every multiple of 4096.
  - `NoteKeepWatchBlocked()` logs one line:
    `C1 keep-watch: blocked for this process (native renderer); every protect takes the normal path`.
- **V3:** `NoteKeptProtect(address, size);` just before Protect's keep-watch `return true;`. It runs under G,
  and only when ProtectKeepWatch kept the protect.
- **V4:** `NoteKeepWatchBlocked();` in ProtectKeepWatch's latch check. It runs under G, on native only. This
  is gate C's positive check.
- **V5, state line:** in Memory::Initialize, before the arena breadcrumb. It prints only when
  `physical_protect_keep_watch` is on, and it is one of:
  - `C1 keep-watch: on, but blocked for this process (native renderer)` (INFO);
  - `C1 keep-watch: on, but physical_protect_hold_global_lock is off, so no protect is kept` (WARN). This is
    the optional "on without fix (i)" warning.
  - `C1 keep-watch: on (with physical_protect_hold_global_lock)` (INFO).

## Why kInitOnly and not kRequiresRestart

What the SDK does (cvar.cpp:300-338, cvar.h:136-139, settings_overlay.cpp):

- **`kRequiresRestart` doesn't block a runtime set.** The setter applies the new value at once and only calls
  `MarkPendingRestart`. The settings overlay labels the entry "[restart]". Protect reads keep_watch on every
  call, so a flip would take effect immediately.
- **`kInitOnly` sets are rejected only after `FinalizeInit()`, and nothing calls `FinalizeInit`** (checked in
  SDK src and rexlego/src). So every launch-time set still works:
  - the harness `-Cvar`, which writes the startup toml (run-game.ps1 `Set-Toml`);
  - the toml itself (`LoadConfig`, rex_app.cpp:224 and :277);
  - the command line (`cvar::Init`);
  - env.

  There's a precedent: `log_level_gate` (kInitOnly) worked through `-Cvar` in window 3.
- **The settings overlay shows kInitOnly entries read-only** (`settings_overlay.cpp:531`). So neither cvar can
  be flipped there mid-run.

Why both cvars: Agent 10 (b2r L1189) points out that a mid-run toggle could keep a form-1 state from before
fix (i) went on, and C1 would never heal it. Two cases do this:
- C1 is on, and fix (i) is turned on mid-run;
- fix (i) is turned off and back on.

v1's NOTE claimed a runtime flip was harmless for C1. That claim was wrong and is withdrawn.

What's still open:

- **The developer console** (`console_overlay.cpp:221`, `SetFlagByName`) can still set any cvar, init-only
  ones included. Closing that needs a code latch: read both cvars once in Memory::Initialize and use the
  latched values in Protect. I didn't add it because it's more logic to rate. It's available if Agent 10
  wants it.
- **v1's `physical_protect_keep_watch_verify` keeps kRequiresRestart.** Flipping it mid-run can only produce
  false K lines in a verify run, so it isn't a safety issue.

## Behaviour

- **OFF (the default) runs the same code path and logs the same as v1.**
  - V3 and V4 are on the ON branch only: ProtectKeepWatch runs only after
    `owns_lock() && !old_protect && REXCVAR_GET(physical_protect_keep_watch)`.
  - V5 costs one cvar read at init.
  - V1 and V6 change only cvar metadata. Both entries become read-only in the settings overlay. For #5's cvar,
    that is v2's only visible change at the default.
- **The init line is valid.** Cvars are loaded before Memory::Initialize, which already reads `protect_zero`.
  On native, rexlego's namespace-scope initializer sets the latch before `main`, and the atomic is
  `constinit` (§28 C), so the init line reads "blocked" there.
- **Log volume:** at most 12 lines for the first 4096 kept protects (the first one, plus 11 powers of two from
  2 to 2048), then 1 line per 4096. The blocked line prints once per process.
  - All of these lines log under G. That is an existing pattern: the logger's lock is a leaf.
    AccessViolationCallback runs with G held and already logs "Recovered stale physical page protection" and
    "Unhandled guest physical write fault" (v2 xmemory.cpp L657 and L672).
- **Count accuracy:** below 4096, the last `kept so far` line gives the total to within a factor of 2; above
  it, to within 4096. Gate D only needs "≥ 1", which the first-kept line gives.
- **In ON-run logdiffs, these lines are NEW by design.** OFF runs show no difference.

## Not done, and why

- **No shutdown total.** Since #27, some exit paths can `_Exit` without running destructors or atexit handlers,
  so a total printed at shutdown would sometimes be missing. The running-count lines don't depend on the exit
  path.
- **No init-time code latch.** See "What's still open" above: the developer console can still flip the cvars.
- **No per-reason decline counts.** Gate D only needs the kept count. Counting why ProtectKeepWatch declined
  (range, page state, gpu_written, provide_data) would add code on the ON path without serving any gate.

## Apply order and landing

- **On top of S4a** (which has #7, #8 and #5):
  1. SDK: `keep-watch-v2.diff`, which replaces v1's `keep-watch.diff` (5 SDK files, S4a output → C1 v2).
  2. Game repo: v1's `keep-watch-rexlego.diff`, unchanged.
- For reference, from the live tree: `chain-live-to-c1v2.diff` (diag + P2 + fix (i) + C1 v2 in one diff).
- Landing needs the same steps v1 needed (§28):
  - a full SDK install plus a game rebuild, because xmemory.h and shared_memory.h gain members;
  - then re-pinned native baselines (native3d, nativeB), because the rexlego hunk changes the native
    fingerprint once.

## Test plan (once C1 ON is allowed; devoff only)

- Set both cvars at launch: `-Cvar 'physical_protect_hold_global_lock=true;physical_protect_keep_watch=true'`.
  The settings overlay then shows both as read-only. Don't set either from the developer console mid-run.
- Cover the title, the menu walk and one level load (§28: an ON run must include a level load).
  - Expect `on (with physical_protect_hold_global_lock)` at init, then a `first kept protect` line. The last
    `kept so far` line gives the count (gate D, and A's positive control).
  - Gate D's zero lines still apply: no "Recovered stale physical page protection" and no "Unhandled guest
    physical write fault" lines.
- Native with both cvars on (gate C's positive check): expect `on, but blocked` at init, one `blocked for
  this process` line, and no `kept` line.
- keep_watch on without the hold: expect the WARN line at init and no `kept` line.

## Checks

- **`make_c1v2.py`: RESULT PASS (13:49:32).**
  - v1's 12 copies and 3 diffs match v1's HASHES.txt, and the 7 live bases match.
  - Each of the 6 anchors matched exactly once. The 38 added or changed lines are at most 96 columns, with no
    trailing space and no tab; LF only.
  - `git apply --check` exits 0 on the live SDK for diag, P2, fix (i) and `chain-live-to-c1v2.diff`, and on the
    live game repo for `keep-watch-rexlego.diff`.
  - On scratch, outside any work tree:
    - v1's xmemory.cpp + `v1-to-v2.diff` = v2's xmemory.cpp;
    - the 4-step chain #7 → #8 → #5 → `keep-watch-v2.diff` on copies of the live files reproduces every staged
      file.
- **Syntax check (`bench/agent12/s4c1v2_syntax.ps1`): RESULT PASS.**
  - Report: `syntax-20261122-134952.txt`, 13:49:56.
  - Setup: BelowNormal, 1 thread, no PCH, no objects. The control is v1's xmemory.cpp and the candidate is v2's;
    both compile with the staged C1 headers first, and those headers equal HASHES `new`.
  - Control: exit 0, 22.0 s, 1 diagnostic. That is the known `unused parameter 'global_lock_locked_once'`
    (:2471).
  - Candidate: exit 0, 14.5 s, the same 1 diagnostic (:2511). Its sha DC23757A… equals HASHES `new`.
  - No new diagnostics.

## Files

| File | SHA-256 |
|---|---|
| `v1/sdk/src/system/xmemory.cpp` (= C1 v1 new, 117,939 B) | 6C801EB2BA7D0D07A476C0B0E0B659F14D574CEB33D86530768AC0FA097B080D |
| `new/sdk/src/system/xmemory.cpp` (C1 v2, 119,957 B) | DC23757AC206FCC51F03B89C0A77F8EFCDB372B138C5D72600C230C295EC8CFD |
| `v1-to-v2.diff` (90 lines, 5 hunks, +43/-3) | CE5D9DAEA4949C7DFC3F5CDFA632D4B56C555633BD3AFC826680D5B1B7325A09 |
| `keep-watch-v2.diff` (571 lines, 20 hunks, +403/-4) | 418D3D39947DB1461974851ABAEAE933BC6460D85448F52EA743CB1CDE39169D |
| `chain-live-to-c1v2.diff` (809 lines, 25 hunks, +596/-3) | DC882A5111EF169EDFFE6875EEF8FD1EBDE2730F8D401606F1AD313C1C0FF470 |
| `keep-watch-rexlego.diff` (v1's, reused) | 4D0C10794188CF450046D42B249C9C46D009EE9F4F1B82116954857FA70838BD |
| `make_c1v2.py` | 8AC1412BD789D49192B439C41E00289B1BB3D0DDED1F8BB5C4139FC393E5B563 |
| `syntax-20261122-134952.txt` | B121A7C5A15F3C5D49DC1CD8BFFE5305373F096173C2568F7FE0D8B6CFCDE1E0 |

The other four `new/sdk` files equal v1's new copies: xmemory.h 5A70782E…, shared_memory.h 82A66445…,
primitive_processor.cpp 470BA4BE… and shared_memory.cpp A4A31038…. Full hashes are in `HASHES.txt`.
