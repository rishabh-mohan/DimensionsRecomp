# S3T-12: C1 verify-only fix (RESUME §6 item 2, option (b)), staged

M12 (successor of Agent 12), 2026-11-25 ~01:35. **Staged only: not built, not applied to any tree, not rated.**
Paths are relative to the workspace root.

## Files

| file | sha256 (prefix) | what |
|---|---|---|
| `build/agent12/session3/c1-verify-fix/c1-verify-fix.diff` | 66B9254E2E13334E | the fix, SDK-relative headers (`a/src/graphics/shared_memory.cpp`), +12/−0, one hunk |
| `.../c1-verify-fix/orig/src/graphics/shared_memory.cpp` | A4A31038ABDFF94A | before = live rexglue-sdk 5350b1d = `build/agent2/snap1` copy = the file b2r §41 checked |
| `.../c1-verify-fix/new/src/graphics/shared_memory.cpp` | F38B47CB411BEEB8 | after |
| `build/agent12/session3/make_c1_verify_fix.py` | see SESSION3.md | makes orig/new/diff and runs the apply check |
| `.../c1-verify-fix/scratch-apply/` | | the throwaway apply-check tree (its own `git init`, autocrlf false) |

Apply check (01:29, `make_c1_verify_fix.py`, exit 0): on a fresh copy of the live file in a throwaway repo,
`git apply --check` rc 0, `git apply` rc 0 ("Applied patch src/graphics/shared_memory.cpp cleanly"), result
byte-identical to `new/`, `git apply -R --check` on the result rc 0; live file unchanged afterwards (A4A31038…).
The `build/agent2/snap1/DimensionsRecomp/rexglue-sdk` copy has the same hash, so the diff applies there too.
Apply in a tree without `.git` with `git apply --directory=...` from the tree's parent or by copying `new/`
(see RESUME §7 step 3 on "Skipped patch" when the tree has no `.git`). No compile or syntax check was run (no compiles
allowed now); `std::fill_n` needs `<algorithm>`, already included (shared_memory.cpp L12).

## The change

In `SharedMemory::MakeRangeValid`, inside the global-lock (G) scope that sets the valid bits (L356-371), after the
valid-bit loop:

```cpp
    if (keep_watch_verify_hashes_) {
      std::fill_n(&keep_watch_verify_hashes_[valid_page_first],
                  valid_page_last - valid_page_first + 1, uint64_t(0));
    }
```

## Why it fixes the race (row 7's F 92)

The race (Agent 12, 22:31 on Nov 22; confirmed by Agent 10's subagent B, b2r §41 L2456-2467):
1. MakeRangeValid sets a page valid under G (L356-371) and releases G (P2 off).
2. It arms the watch (L373-377; xmemory.cpp L799-808, each view takes and drops G).
3. Only then does it re-hash the page (KeepWatchVerifyRecord, L381-383 → L703).
4. A guest write fault between 2 and 3 enters MemoryInvalidationCallback with G (L577) and runs the F check
   (L581-583) on a valid page whose hash is from the page's *previous* upload. Invalidation never clears hashes. The
   page is being re-uploaded because the CPU changed it, so the old hash mismatches → a false F.

With the fix, step 1 also sets the page's hash to 0 under the same G hold. KeepWatchVerifyCheck skips hash 0
(L719), so a fault in the gap skips the page; Record (under G, L686) then writes the fresh hash. The invariant
becomes: **a valid page's hash is 0 or was recorded after its latest validation.** It holds because valid bits are set
only at L367 (subagent B: the other writes at L63/L114/L124/L134 only clear), hashes are written only at L703 and
here, and every read and write of the hash array is under G (Record L686, F L577, K under the caller's G per L639).

## What it changes, and what it doesn't

- **Verify off (the default; every timed arm):** `keep_watch_verify_hashes_` is null (allocated only by the first
  Record, L687-688), so the cost is one null test under a lock already held. No behaviour change. Still a change in
  the default code path, so it needs Agent 10's (M10's) rating like any SDK change.
- **P2 on (p2fc + verify: gate A, s4bLV):** G is held from L351-354 until MakeRangeValid returns, so no fault or
  protect can see the zeroed hash before Record overwrites it. Nothing observable changes; s4bLV's meaning is
  unchanged on a fixed bin.
- **P2 off + verify (row 7, s4bV0):** in the gap, F *and* K skip the page. K skipping means a keep-watch protect in
  the gap takes C1's keep path instead of being refused against a stale hash; that is exactly C1's non-verify
  behaviour, which is what we want to measure.
- **Detection lost:** only writes that would land without a fault *inside* the gap (a few µs per upload). A real miss
  there was never detectable: the stale hash made every gap fault look like a miss.
- **Side effect, the runtime-flip false F/K (b2r §41 L2470, L2483):** the zero is gated on the pointer, not the cvar,
  so after a runtime flip to off every re-validated page gets hash 0 and stays skipped. That closes the runtime-flip
  false F/K for re-uploaded pages. Keep the rule "never flip verify at runtime" anyway until M10 rates this.
- **Not addressed (b2r §41 L2468-2471):** the two non-race F sources remain and still give the same line: a guest
  write fault during a file read (xfile.cpp L266-295) and any real miss (host write through the physical alias that
  invalidates late/never, or an alias view the watch doesn't cover). So F > 0 on a fixed bin is a real signal.
- **Native builds:** untouched in effect (C1 is latched off). The native fingerprint inputs
  (`build/agent2/snap1/NATIVE-INPUTS-N1*-2055.tsv`) list no rexglue-sdk file, so no re-pin.

## Bin needed (M2's build, when the Overseer allows one)

Only `rexgpu-xenos.dll` changes: `src/graphics/shared_memory.cpp` compiles into
`snap1-sdk/src/graphics/CMakeFiles/rexgpu-xenos.dir/` and no header changes. Proposal:
1. Apply the diff to the snap1 SDK copy (A4A31038… → F38B47CB…), rebuild target `rexgpu-xenos` only, Release,
   ≤ 2 threads, Idle.
2. Stage `build/agent2/devoff4bv-bin` = devoff4b-bin's 7 files with only `rexgpu-xenos.dll` replaced; MANIFEST as
   usual (record that the exe, rexruntime.dll and the rest are byte-identical to devoff4b-bin's).
3. Don't overwrite `snap1-sdk/install/bin/rexgpu-xenos.dll` (E3CB99CF…), which devoff4b-bin and native4b-bin share,
   or restore it afterwards, so the S4b reference stays reproducible. M2's call.
4. Apply check M2 should re-run first: `git apply --check` of the diff against the snap1 copy; expect A4A31038… before.

## Row-7 re-run plan (needs RUN GO, a quiet host, M10's rating of the diff and the bin)

All rows: L route `build\agent3\toypad\routes\level-l.txt`, `-Seconds 600`, toypad, quiet host (no build, no
Minecraft, no other game), checked with `s4b_check.py` and M3's `f10_rule.py` (finding-10 rule; see GATE-CHECKLIST.md).

| id | bin | cvars | purpose | expectation |
|---|---|---|---|---|
| s4b07r (queued by M3) | devoff4b | fix (i) + C1 + verify (= row 7) | does the race reproduce on a quiet host? | F > 0 (race) |
| s4bV0 (queued by M3) | devoff4b | fix (i) + verify, C1 **off** | option (a): the race without C1 | F > 0 on pages ~01AE8000-022BF000, the write-faulting thread (row 7: XThread90B8) |
| **s4b07f** (new) | devoff4bv | fix (i) + C1 + verify (= row 7) | **option (b): C1 without P2, race removed** | **F 0, K 0** if C1 is clean |
| s4bV0f (new, recommended) | devoff4bv | fix (i) + verify, C1 off | control for the fix itself | F 0 |

Queue-line form (M3 owns the queue; for the Overseer to relay), same as s4b07r but:
`-BinDir build\agent2\devoff4bv-bin -Tag s4b-07f-c1v-level-vfix` and, for s4bV0f,
`-Tag s4b-V0f-c1off-verify-level-vfix` with `physical_protect_keep_watch=false`.

**Positive control (must hold or the row is INCOMPLETE, not PASS):** "C1 keep-watch: on (with
physical_protect_hold_global_lock)" ×1; "C1 keep-watch: first kept protect at" present; kept count reaches the
row-7 level (32768) (s4b07f only); "C1 verify: on." ×1; the route reaches story-load (row 7: 104/119 steps at the
cap). For s4bV0f: no keep-watch lines, "C1 verify: on." ×1.

**Reading:**
- s4b07f F 0 / K 0, s4bV0f F 0 → C1 without P2 is clean on this route; item 2's option (b) is settled
  (route-limited, like gate A). Report the row with s4b07r's F count: if s4b07r is also F 0 on the quiet host, the race
  needs load to show, so s4b07f's F 0 is weaker evidence (it didn't remove anything measurable) → note it and keep
  "C1 ships as p2fc" until the s4bLV row passes.
- s4b07f F > 0 and s4bV0f F > 0 on the same pages/thread → a non-C1 source (file-read path first: compare F times with
  the INSTALL*.DAT bursts); not a C1 failure, but the verify tool isn't clean without P2 → read with Agent 10's two
  non-race sources.
- s4b07f F > 0 and s4bV0f F 0 → **C1 suspect** (a kept watch missed a write). C1 stays p2fc-only; send the F pages,
  threads and times to the Overseer; no C1-without-P2 arm anywhere.
- s4b07f K > 0 → K refused a keep after a real change; same as F for the verdict (C1 suspect unless s4bV0f shows the
  same pages).
- Any STUCK-LOCK: finding-10 rule (GATE-CHECKLIST.md); non-finding-10 → FAIL, re-run is the Overseer's call.

Ordering: s4bV0f before s4b07f (cheapest refutation first), both after s4b07r/s4bV0 if those run anyway.
Estimate: 2 × ~10 min of runs + ~5 min of checks.
