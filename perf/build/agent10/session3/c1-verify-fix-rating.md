# C1 verify-only fix rating (devoff4bv; rows s4bV0f / s4b07f)

M10 (successor of Agent 10), session 3. Read-only work on 2026-11-25, 01:44-01:50: nothing was built or run. I applied the diff to a scratch copy only, then deleted it.

**Question (Overseer, 01:37).** Is it SAFE to build devoff4bv with the C1 verify-only fix and to run rows s4bV0f / s4b07f?

**Files rated** (`build/agent12/session3/c1-verify-fix/`):

| file | sha256 (first 16) | size |
|---|---|---|
| `c1-verify-fix.diff` | 66B9254E2E13334E | 1285 B (+12/-0, one hunk) |
| `RATIONALE.md` | 73BD5147B1BBC6E6 | 8995 B, 122 lines |
| `orig/src/graphics/shared_memory.cpp` | A4A31038ABDFF94A | - |
| `new/src/graphics/shared_memory.cpp` | F38B47CB411BEEB8 | - |

**Base.** `DimensionsRecomp/rexglue-sdk` HEAD is 5350b1de99... For `src/graphics/shared_memory.cpp`, `git hash-object` on the worktree file equals `HEAD:` (59a636d7, the diff's index line). The worktree, `orig/` and the snap1 copy all hash A4A31038. `git -c core.autocrlf=false apply --verbose` on a scratch copy gave "Applied patch ... cleanly", and the result hashes F38B47CB == `new/`.

`src/graphics/shared_memory.cpp` is not the file #19 touches; #19 changes `src/graphics/d3d12/shared_memory.cpp`. So there is no textual overlap with #19.

## Verdict

- **Code: SAFE.** No BLOCKER, no SHOULD on the code.
- **Build devoff4bv: SAFE-IF**:
  1. Builds only when the Overseer allows them: M2, Idle, ≤ 2 threads, target `rexgpu-xenos` only. `shared_memory.cpp.obj` is in `snap1-sdk/src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/`, and no header changes.
  2. Check the before-hash A4A31038 on the target tree first. Then copy `new/` (F38B47CB), or use `git -c core.autocrlf=false apply` from the tree root. Never use `git -C <sdk>` on a tree without `.git` ("Skipped patch", exit 0).
  3. Keep the shared reference intact. `snap1-sdk/install/bin/rexgpu-xenos.dll` (E3CB99CF) is part of devoff4b-bin, devoff4b-cg26-bin and native4b-bin. After staging, the MANIFESTs of devoff4b-bin (DE11A914), devoff4b-cg26-bin (917AE86E) and native4b-bin must still verify. Either build into a copy, or restore the installed DLL and re-hash it (S1).
  4. Stage `build/agent2/devoff4bv-bin` as devoff4b-bin with only `rexgpu-xenos.dll` changed. The MANIFEST shows exe DFBE1D43, rexruntime A33801D1 and the rest byte-equal to devoff4b-bin, and a new DLL hash ≠ E3CB99CF.
- **Rows s4bV0f, then s4b07f: SAFE-IF**:
  1. RUN GO plus the quiet-host gate (`go-quiet`), on the hidden desktop. s4bV0f runs before s4b07f, and both share one host state with s4b07r / s4bV0 if those run tonight (RUNPLANS (b)).
  2. Set the cvars at launch only. Never flip verify at runtime, even though the fix also covers re-uploaded pages after a flip (RATIONALE L65-67).
  3. `s4b_check.py` must know the new ids before they run: s4b07f gets s4b07's proofs, s4bV0f gets the s4bV0 branch, and both check that the bin is devoff4bv by MANIFEST. Otherwise the result is INCOMPLETE (S2).
  4. The positive controls of RATIONALE L102-105 must hold, or the row is INCOMPLETE, not PASS.
  5. STUCK-LOCK: finding-10 rule (`f10_rule.py`); anything else is FAIL.
  6. Reading as in RATIONALE L107-118, with one addition: s4b07f F 0 / K 0 settles item 2(b) only for this route. It doesn't make C1-without-P2 a default or a timing arm without a separate Overseer decision; "C1 ships as p2fc" stands until then.
- **The default path (verify off): no behaviour change.** `keep_watch_verify_hashes_` stays null, since it is allocated only in `KeepWatchVerifyRecord` (L687-688), and that runs only with the verify cvar on (L381). The cost is one null test under the G hold MakeRangeValid already takes (L357). Native: C1 is latched off and the pointer stays null; no native rebuild is planned.

## What I checked

### The hunk (new L371-382, inside the L356-371 G scope)
- Placement: after the valid-bit loop, still inside `{ auto global_lock = global_critical_region_.Acquire(); ... }`. So the valid bit and hash 0 become visible together under one G hold.
- Bounds: `length` is clipped to `kBufferSize - start` (L339), so `valid_page_last ≤ (kBufferSize - 1) >> page_size_log2_`. The array has `kBufferSize >> page_size_log2_` entries (L688). `page_size_log2_` is set once (L51). The count `valid_page_last - valid_page_first + 1` is ≥ 1 and stays in range.
- Types: `std::unique_ptr<uint64_t[]>` (shared_memory.h L203) supports `operator bool` and `operator[]`. `std::fill_n` with `uint64_t(0)` is well-formed, and `<algorithm>` is already included (RATIONALE L22; not compiled here).

### The invariant: "a valid page's hash is 0 or was recorded after its latest validation"
- Valid bits are set only at L367; every other write to `system_page_flags_valid_` clears bits (grep of shared_memory.cpp, d3d12/shared_memory.cpp, shared_memory.h).
- Hashes are written only at L703 (Record, under G at L686) and by the new hunk (under G at L357).
- Hashes are read only in `KeepWatchVerifyCheck`. F is called under G (L577 → L581-583). K is called by `MemoryKeepWatchGuard` with G held by the caller (L637-639, L662). Every access is under G, so no torn or stale reads.
- `KeepWatchVerifyCheck` skips hash 0 (L719). So a fault or protect in the gap between L371 and L686 skips the page, and Record then stores the fresh hash.
- Race closed: before the fix, a fault in that gap compared against the page's previous upload hash. Invalidation never clears hashes (L607-617), so this gave a false F (row 7's F 92) and could give a false K. With P2 on, G is held from L353 through Record, so nothing observable changes, and s4bLV keeps its meaning.
- Detection given up: only writes that hit the gap. Before the fix those already compared against a stale hash, so they couldn't tell a real miss from the race. RATIONALE L63-64 agrees.
- Both callers are fine: `MakeRangeValid(..., true)` from the GPU-written path (L324) zeroes pages that Record would set to 0 anyway (L696-697); the CPU-upload path is the one that matters.
- Not addressed (RATIONALE L68-70, b2r §41): the file-read fault path and real misses can still give F. So F > 0 on devoff4bv is a real signal, and the reading table covers it.

## Findings

- **S1 (SHOULD, build).** Make keeping E3CB99CF reproducible a hard step, not "M2's call" (RATIONALE L82-83). It is in four staged bins' MANIFESTs, including W10's two arms, and a silent overwrite would break the bin checks tonight.
- **S2 (SHOULD, runner).** `s4b_check.py` needs explicit branches for s4b07f / s4bV0f, including the devoff4bv bin check, before the rows run. That is M3's edit, and it's a runner change for rating.
- **N1.** RATIONALE L20 suggests the `--directory` form. As with #19, copying `new/` is simpler and avoids the CRLF trap.
- **N2.** RATIONALE cites b2r by line number (L2456-2483); cite by § (§41).
- **N3.** The new comment says "Valid bits are set only above". True today; a future second valid-bit writer would need the same zeroing. Consider an assert-free note at L367 as well.

## Read / Sent

Read: the 4 files in the table; `DimensionsRecomp/rexglue-sdk/src/graphics/shared_memory.cpp` L320-400, L560-740 and the greps above; `build/agent3/session3/RUNPLANS.md` L9-30, L81-82; `build/agent3/s4b/queue.jsonl` L50-51 (s4b07r / s4bV0 cvars). Sent: this verdict to the Overseer.
