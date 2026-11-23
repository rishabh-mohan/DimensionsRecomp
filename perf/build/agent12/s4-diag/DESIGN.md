# S4 u diagnostic: `shared_memory_upload_hash_log` (Agent 12, task #27)

**Status:** staged only, not applied, not built. Logging only; the cvar defaults to OFF. **Agent 10 (06:44, §20 in `perf-notes/agent10-batch2-review.md`): SAFE at default OFF; ON is SAFE for functional runs.**

**Build:** Agent 2 builds this only when Agent 1 schedules it, after the user agrees to the S4 plan, like P1 and P2.

## Files

| file | what |
|---|---|
| `upload-hash-log.diff` | Diff against the live `DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/shared_memory.cpp`. 4 hunks, paths relative to the SDK root. `git -C DimensionsRecomp/rexglue-sdk apply --check` passes (06:10). |
| `orig/shared_memory.cpp` | Copy of the live file at 06:10 (14514 B, LF, git clean; last commit 71782a3; SDK HEAD c5fe668, the S3 commit; this file is the same as at 90e7ccd). |
| `new/shared_memory.cpp` | Patched copy (20888 B, LF). |
| `HASHES.txt` | sha256 of all three. |
| `syntax-20261122-061249.txt` | Output of `bench/agent12/s4diag_syntax.ps1`: clang `-fsyntax-only` with the exact dev-SDK flags, pristine vs staged. Both compiles exit 0 with 12 diagnostics each, all from existing headers. No new diagnostic. **PASS** |
| `bench/agent12/s4_uhash.py` | Log parser, with `--selftest` (OK). Pass it the run dir: it reads rotated logs oldest first. |

**sha256:**
- live = orig: `B120D07C6709D0D2A7836B532ED06B2032A418CBD4A71808CD318C7E6EB6CFBC`
- new: `BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587`
- diff: `D290530197427138029FF34EE8B1BBBEDE26340AA85D0AE4EABB00DC0CEE9CEF`

## What it measures

**u** is the share of each re-upload that copies bytes the GPU already has, i.e. bytes unchanged since that page's previous upload.

When the cvar is on, every successful `D3D12SharedMemory::UploadRanges` call (GPU Commands thread) does the following for each page in `upload_page_ranges`, after the upload loop:
- **Hash:** XXH3-64 over the guest copy, read through `memory().TranslatePhysical(...)`. That is the cached physical view the memcpy just read, with the same pointer arithmetic. It never reads the write-combined upload mapping.
- **Classify:** compare with the page's hash from its previous upload. Each page is a *first upload*, *unchanged* or *changed*.
- **Block bookkeeping, per 256 KB block:**
  - blocks with uploads;
  - blocks with at least one changed page;
  - re-uploaded pages inside changed blocks.

  256 KB is the granularity at which P1 would fault. A non-exact (fault) invalidation is widened to 256 KB by both callbacks:
  - SharedMemory: `shared_memory.cpp:531-551`, which stops at GPU-written pages;
  - PrimitiveProcessor: `primitive_processor.cpp:1439-1440` (`kCacheBucketSizeBytes` = 1 << 18).

  TriggerCallbacks unwatches the intersection of the two (`xmemory.cpp:2355-2362`).

**Log line.** One line per frame that had uploads, at `[info] [gpu]`. The line for frame F is printed at the first upload of a later frame. So frames without uploads have no line, and the last frame before exit is never printed.

```
S4 upload hash: frame 4711 calls 6 ranges 41 pages 5120 (20480 KB) first 12 unchanged 4980 changed 128 blocks 80 changed_blocks 9 pages_in_changed_blocks 576 u_page 0.9748 u_block 0.8873
```

| field | meaning |
|---|---|
| frame | `GetCurrentFrame()` (`frame_current_`, starts at 1). Not ReportSlowFrame's `#N`. |
| calls / ranges | UploadRanges calls and page ranges in the frame |
| pages (KB) | pages uploaded (4 KB pages) |
| first | pages hashed for the first time; excluded from u |
| unchanged / changed | re-uploaded pages identical to / different from their previous upload |
| blocks | distinct 256 KB blocks with uploads |
| changed_blocks | distinct 256 KB blocks with at least one changed page |
| pages_in_changed_blocks | re-uploaded pages that sit in changed blocks |
| u_page | unchanged / (pages - first); -1 if the frame only had first uploads |
| u_block | 1 - pages_in_changed_blocks / (pages - first); -1 if the frame only had first uploads |

## How to read u

- **Window value:** u = sum(unchanged) / sum(pages - first), weighted by pages. It is not the mean of the per-frame values.
  - Use the steady-state window, as in Agent 5's parser: 70-220 s after the first frame. First uploads dominate the loading phase.
  - `s4_uhash.py` does this. Pass it the run dir: it reads rotated logs oldest first (game.N.log ... game.1.log, then game.log). It takes its time base from the ReportSlowFrame lines when `slow_frame_log_ms` is set; otherwise it uses `--frames A:B`. If the first slow-frame index is over 50, the oldest log was lost and the window is shifted: it warns, and `--frames` is the fallback.
- **u_page** is the upper bound on what *any* write-watch scheme could skip at page granularity.
- **u_block** is the same for P1 at its 256 KB fault granularity. This is the number to use for P1.
- **Both are upper bounds.** The hash sees unchanged *bytes*, not unwritten pages. A guest rewrite with identical bytes counts as unchanged here, but under P1 it still faults, invalidates its block and re-uploads.
- **P1's downside, from the same lines:**
  - faults per frame: `changed_blocks` is the lower bound (one fault per written 256 KB block per view). `blocks` is the upper bound in steady state, because a block can fault at most once per upload and re-arm cycle.
  - re-upload per frame: `pages_in_changed_blocks` is the lower bound. `changed_blocks` x 256 KB is the upper bound. Block widening can make P1 re-upload pages next to a small lock that today's exact lock-time invalidation leaves valid.
  - The parser prints both bounds and the fault time at 5/8/15 µs per fault.
- **Decision guide** (S4.8 in `perf-notes/agent12-io-memory.md`):
  - a-vol (06:31) measured ~3.76 MB/f invalidated in ~1.87 invalidations per frame, so P1's faults are at most ~17 per frame, ≤ 0.25 ms/f. That is less than Main's 0.54-1.02 ms/f saving at any u, so u_block decides.
  - u_block >= 0.25: go to the A/B. P1's GPU Commands saving is about u_block x UploadRanges (3.64/3.85 ms/f a/b).
  - u_block < 0.1: no-go for P1; take P2 and Agent 5's memcpy items instead.
  - In between: build it behind the cvar and let the A/B decide.

## Cost when on

- **Hashing:** one XXH3-64 pass over every uploaded byte, on the GPU Commands thread, after the copies are recorded.
  - Speed: ~10-15 GB/s with the default SSE2 build, with the data partly still in L2/L3 from the memcpy (~5 GB/s from DRAM).
  - a-vol measured ≤ 3.76 MB/f invalidated, so the re-uploads are about that, and the hash costs roughly **+0.25-0.4 ms/f** (≤ ~0.75 ms/f from DRAM) on the critical thread. (The earlier +1-3 ms/f came from my 15-30 MB/f estimate, which a-vol showed was 4-8x high.)
  - **Use functional runs only, never timing arms.** The extra GPU-thread time can change frame pacing. Agent 10: that can bias u slightly low, so cross-check pages per frame against an OFF run (a-vol: ~3847 KB/f invalidated).
- **Bookkeeping:** a few ns per page. The per-frame flush is one 2048-block scan plus 3 memsets of 8.5 KiB, ~1-2 µs.
- **Memory:** 1 MiB of hashes and a 16 KiB bit set, allocated at the first call with the cvar on. Plus ~8.5 KiB of static counters (.bss).
- **Lock:** one `std::mutex`, taken only when on. It is uncontended, because UploadRanges runs only on GPU Commands.
- **Log volume:** one line per frame, about the same as `slow_frame_log_ms=1`, so the run plan's log roughly doubles (~14 MB in 5 min against a-vol's ~9 MB). game.log rotates at 5 MiB; pass the run dir to the parser.

## Off path: why it stays output-identical

- **Upload loop:** byte-identical, with no original line changed, moved or reordered. Hunk 4 of the diff is a pure addition after the loop, just before `return true`. The error path (`return false`) is unchanged.
- **Runtime cost when off:** one cvar load and one untaken branch per *successful* UploadRanges call, at most a few dozen per frame. No lock, no allocation, no state touched. The static state (`upload_hash_log`) is constructed at startup and never accessed.
- **Hunks 1-3** are additions outside function bodies:
  - the includes `<mutex>` and `<rex/hash.h>`. `pipeline_cache.cpp` in the same directory includes the same header. It defines `XXH_INLINE_ALL`, so XXH3 is static inline and nothing changes at link time.
  - the cvar definition;
  - an anonymous-namespace struct and 3 helpers.
- **With the cvar on**, GPU-visible results are unchanged too. The diagnostic only reads guest memory and writes its own state. It does not touch the upload buffers, the command list, valid bits, watches or guest memory.

## Caveats

- **Race:** a guest write between the memcpy and the hash can misclassify that page. The window is the rest of the same UploadRanges call. This is rare and acceptable for a diagnostic.
- **Toggling at runtime:** while the cvar is off, pages keep their last hash, so the first comparison after re-enabling is against an older upload. Set the cvar at startup for clean numbers.
- **Repeats:** a page uploaded twice in one frame counts twice; the second upload compares against the first.
- **Coverage:** only CPU-to-GPU uploads through UploadRanges are seen. Memexport and resolve writes don't upload, and GPU-written pages are never uploaded from the CPU copy.

## Agent 10 rating checklist

1. **Off path:** hunks 1-3 only add code outside functions. Hunk 4 only adds the `if (REXCVAR_GET(shared_memory_upload_hash_log))` block after the loop. No original line changed (diff: 179 lines, 0 removed lines).
2. **Bounds:**
   - page indexes are clamped to `page_hashes.size()` (the 512 MB buffer >> page_size_log2);
   - block index < 2048 (`kBufferSize >> 18`);
   - `TranslatePhysical(first << log2)` plus `page_size * i` stays inside the same contiguous physical mapping the memcpy reads.
3. **Threading:** all state is under `upload_hash_log.mutex`. `REXGPU_INFO` runs under it, and logging never re-enters UploadRanges.
4. **No GPU-visible effect when on:** see "Off path" above.
5. **Syntax check:** `bench/agent12/s4diag_syntax.ps1` passes (report above). Rerun it with `-Live` after an apply; it checks the live hash against `staged`.
6. **Kill switch:** the cvar is off by default. `--shared_memory_upload_hash_log=true` turns it on for one run.

## Run plan

This needs Agent 1 to schedule it: a functional slot through Agent 8, after the S4 OK.
- **Build:** devoff2 plus this patch.
- **Cvars:** `--shared_memory_upload_hash_log=true --slow_frame_log_ms=1 --framerate_limit=0`. The second gives the parser its time base, and the same log also gives Agent 5's invalidation counts.
- **Route:** the same as a-vol (`bench/agent5/matrix-s4-invalvol.json`), measured over 70-220 s.
- **Analysis:**
  - `python bench/agent12/s4_uhash.py <run dir> --json build/agent12/s4/uhash.json`
  - `python bench/agent5/s4_slowframe.py <run dir>` on the same log.
