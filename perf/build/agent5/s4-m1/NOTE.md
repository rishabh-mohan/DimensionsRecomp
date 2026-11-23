# S4 M1: non-temporal copy into the upload buffer (S4-DRAFT #11)

Agent 5, 2026-11-22, board run 2. The M1 diff is staged only: not applied to the live SDK, not built into a bin, not run in the game. Rated by Agent 10 (b2r row 34, §33 and its addendum): SAFE at the default, ON is SAFE to test. The microbench's correctness gate ran at 14:12 (task #18): **PASS** (test plan step 2).

- **Diff:** `m1-nontemporal-copy.diff` (5 hunks, +72 -3) against SDK `src/graphics/d3d12/shared_memory.cpp` **after #7**: base BB0838CE… (= `build/agent12/s4-diag/new`). Apply with cwd = SDK root, after #7. Hashes and apply checks are in `HASHES.txt`. Made by `bench/agent5/s4m1_mkdiff.py`.
- **Switch:** `shared_memory_upload_nontemporal_copy`, bool, default **false**, category GPU/D3D12. Lifecycle is the default (hot reload). It is read once per UploadRanges call, so a toggle takes effect at the next call.
- **Syntax:** PASS. This was a syntax-only clang run with the dev-SDK Release flags, using `bench/agent5/s4m1_syntax.ps1` (Agent 12's method, PCH dropped). base and new both exit 0, both show the same 12 header warnings, and new adds no diagnostics. Report: `syntax-20261122-132054.txt`.
- **Order:** S4-DRAFT L166 puts #9 P3 before #11 M1 in this file. If P3 lands first, M1 must be rebased onto base + P3 (the "flag" and "copy" hunks are in UploadRanges).

## What changes

- **Off:** UploadRanges runs the original `std::memcpy` (the same call, re-indented into an `else` branch), plus one cvar load per call, before the range loop.
- **On:** the copy into the upload buffer mapping goes through `CopyToUploadBufferNonTemporal(dst, src, size)` instead. It lives in the anonymous namespace; on x86-64 it does the following (on other architectures it is plain `std::memcpy`):
  1. **Alignment (head):** plain `std::memcpy` of `min(size, (64 - (dst & 63)) & 63)` bytes, so the streaming stores start on a 64-byte boundary. `_mm_stream_si128` (MOVNTDQ) faults if the address isn't 16-byte aligned. Copying a head up to 64 bytes also means no cache line gets both plain and streaming stores.
  2. **Body:** `(size - head) & ~63` bytes in 64-byte steps. Each step does 4 × `_mm_loadu_si128` from guest memory (any source alignment) and then 4 × `_mm_stream_si128` to dst, which fills one write-combining buffer.
  3. **Tail:** plain `std::memcpy` of the last `size % 64` bytes.
  4. **sfence:** one `_mm_sfence()` at the end, after head, body and tail. Streaming stores, and plain stores to WC memory, are weakly ordered. The fence makes them globally visible before the function returns: before `D3DCopyBufferRegion` is recorded, and long before `ExecuteCommandLists` lets the GPU read. Today's memcpy relies on later serializing events in the submission path for the same thing.
- **Head and tail never run in practice.** RequestPartial is called with alignment `1 << page_size_log2()` (4 KB), so dst is 4 KB-aligned and the size is a multiple of 4 KB. The source is page-aligned guest physical memory. They are there so the helper is correct for any input.
- **Output-identical:**
  - The same bytes land in the same upload buffer range.
  - The copy still runs after MakeRangeValid (the arm) and before the copy command, so the guest-write race window and the invalidation semantics are unchanged.
  - Nothing reads the WC mapping.
- **Cost when on:** one sfence per chunk. Chunks are at most 2 MiB, so a few per frame.
- No header changes and no other files.

## Why it might help (a hypothesis, not measured)

- In a-prof, memcpy (vcruntime fn_11200 + its rep movsb stub fn_10E40) took 2.9-3.1 ms/f for at most 3.76 MB/f. That is ≤ 1.2 GB/s, about 1 byte/cycle at the slow state's ~1.2 GHz, which is low for a sequential copy.
- One possible cause is the string path's store pattern on WC memory (this machine has an Intel CPU). M1 removes that variable: it does explicit full-line streaming stores.
- If the time goes somewhere else instead (cold guest lines, the TLB, the power state), M1 gains little or nothing.
- Bound: at most (1-u) × 2.9-3.1 ms/f after C1, or 2.9-3.1 ms/f without C1. S4.5 keeps the conservative 10-30% of that until a bench shows more.

## Test plan (when builds and runs are allowed)

1. **Rating (Agent 10):** alignment/head, tail, sfence placement. Also check the `#if REX_ARCH_AMD64` fallback, and that the OFF path is the old memcpy.
   - **Done:** b2r row 34 and §33 (with its addendum). SAFE at the default, and ON is SAFE to test.
   - Before M1 is ON: first the bench check (step 2, PASS at 14:12), then the OFF/ON functional pair (steps 3-4).
   - M1 now comes after C1. It needs a rebase if P3 (#9) lands first.
2. **Microbench in `bench/agent5`, no game:**
   - Copy rate of memcpy vs the helper into a D3D12 upload-heap buffer (WC), at a-vol sizes from 4 KB to 2 MiB.
   - Correctness sweep: dst misalignment 0-63 × sizes 0-300, plus 4 KB and 2 MiB, with guard bytes.
   - Continue only if the helper is clearly faster.
   - Staged: `bench/agent5/m1_copybench.cpp` (AA313906…). It also times a bare rep movsb and the same loop with plain stores, from warm and cold sources, into the upload buffer and into normal memory. It prints the adapter, the upload heap's CPU page property and the CPU's ERMS/FSRM bits. Its copy of the helper is checked against `new/shared_memory.cpp` by `bench/agent5/m1_copybench_syntax.ps1`. Syntax PASS at 13:43 (0 diagnostics, `copybench-syntax-20261122-134316.txt`).
   - **Correctness gate: PASS** (task #18, 14:10:54-14:12:29; Agent 10's condition before ON: exit 0 and 0 failures on both check lines).
     - The bench gained `--check-only`: no rate buffers, no rate part, one PASS/FAIL line per case group (`copybench-checkonly.diff` 41E6A488…, bench F98B935A…). Syntax re-check PASS at 14:10: helper MATCH, 0 diagnostics (`copybench-syntax-20261122-140942.txt`).
     - Built once with `bench/agent5/m1_copybench_check.ps1` (BelowNormal, one clang++ process; the command is in HASHES.txt). exe 92C5FF6E… (40,960 B).
     - Run: `build\agent5\m1_copybench.exe --check-only`, exit 0. Adapter MX570; upload heap WRITE_COMBINE, pool L0.
     - Normal memory: 22/22 groups PASS (154,224 cases). Upload buffer: 18/18 groups PASS (77,168 cases). 0 failures, 0 skipped. Groups: dst offsets 0-63 × sizes 0-300 per source offset (wb 0/1/15/33, upload 0/1), the 7 large sizes (4095, 4096, 4097, 65553, 2 MiB, 2 MiB + 33, 3,936,256), each with guard bytes 0xCD and 0x32.
     - Report: `copybench-check-20261122-141100.txt`.
   - **Rate part:** not run. The machine was loaded, so no GB/s number would be valid. It needs a quiet window: run the exe without `--check-only` or `--skip-rate`.
3. **Functional OFF run** of a bin with M1 built in, compared with the S4a/#7 bin: logdiff NEW 0, same frame hash.
4. **Functional ON runs** (title, Agent 3's menu walk, one level load): logdiff NEW 0, frame hash or screenshot match, no crash.
5. **Timing:** ABBAAB pairs (OFF vs ON) with sys.csv in a user window, plus one profile to see the memcpy share move.

Lands in S4b or later, after the rating. It touches one .cpp, so the build is incremental.
