# W6 draft: upload path (S4-DRAFT L288)

Agent 5, task #18, 2026-11-22 ~14:25. **This is a draft, and nothing in it has been run, not even -PlanOnly.** Agent 8 takes it over after W4b.

- `matrix-w6.json` uses window 4's format. I only read `bench/agent8/run/matrix-window4.json`; its SHA is still 6CA4AC6E….
- **Bin:** every arm uses the placeholder `build/agent2/S4b-bin-TBD`. Set the real S4b bin once it is built, and use the same bin in all four arms.
- **Run** (like `RUN-WINDOW4B.cmd`):

  ```
  run\run-matrix.ps1 -Matrix build\agent5\w6-draft\matrix-w6.json -Only s0,p2,p2f,p2fc -Repeats 3 -ColdShared -NoPrompt
  ```

  - That is 1 shared cold run plus 3 rotated rounds: 13 runs, ~33 min at ~2.5 min per run. Check it with `-PlanOnly` first.
  - Agent 8 may move the file into `bench/agent8/run/` and add a `RUN-W6.cmd`.

| arm | S4-DRAFT | cvars, beyond `framerate_limit=0` |
|---|---|---|
| s0 (ref) | s0 | none: every S4b switch at its default OFF |
| p2 | #8 | `shared_memory_single_hold_rearm=true` |
| p2f | #8 + #5 | p2's + `physical_protect_hold_global_lock=true` |
| p2fc | #8 + #5 + #4 | p2f's + `physical_protect_keep_watch=true`, `physical_protect_keep_watch_verify=false` |

These switches are not in any arm, so they stay OFF everywhere: #7 (`shared_memory_upload_hash_log`), M1 (`shared_memory_upload_nontemporal_copy`), #18/#20, and `slow_frame_log_ms`.

## Gates before W6

1. **C1 v2 rated: met** (Agent 10, 14:12, b2r row 35 / §34).
   - SAFE at the default. ON is SAFE to test.
   - Test rule: set both cvars at launch and never change them mid-run. The dev console can still flip kInitOnly cvars, because `FinalizeInit()` has no caller.
2. **S4b built.**
   - C1 v2 goes in as S4a, then `keep-watch-v2.diff`, then the unchanged rexlego diff (keep its CRLF).
   - S4b also carries P2's counter, #18/#20 and M1 (OFF).
3. **§21 A-D on S4b**, with C1 ON and fix (i) ON, both set at launch:
   - **A:** run C1 ON in verify mode (`physical_protect_keep_watch_verify=true`) over the title, Agent 3's menu walk and one level load. Pass = 0 `C1 verify … changed since its upload` lines. **The level load needs the user's Toy Pad answer.**
   - **B:** met in code (`owns_lock()`).
   - **C:** met (inert on native).
   - **D:**
     - `C1 keep-watch: first kept protect at` is present, so the kept count is at least 1.
     - No `Recovered stale physical page protection` or `Unhandled guest physical write fault` lines.
     - logdiff NEW 0, and the frame hash or screenshot matches.
4. **P2's full-buffer counter totals 0.** Read `memexport full-buffer Nx (total T)` on the slow-frame lines of side run 1 below. If the total is not 0, Agent 1 decides a cap before #8 is timed.
5. **The usual checks before reading fps** (S4-DRAFT L265-269):
   - the slow state, per run;
   - ≥ 6 GB free;
   - Defender below ~5 %;
   - the log lines in the matrix notes.

## Read-out

- **GPU Commands thread ms/f** (`threads.csv`) is the main metric. Main ms/f is the second one, because C1 replaces Main's lock-time protects with write faults.
- **fps and the slowest frames** come from `perf.csv` and `summary.md`.
- Each arm gives a median of 3. A12 asks for at least 5 (S4-DRAFT L264). 3 is enough at C1's expected size, but probably not for P2 or fix (i) alone. If p2f vs p2 is within noise, report "no detectable cost" rather than a figure.
- **Pairs:**
  - P2 = p2 − s0;
  - fix (i)'s own cost = p2f − p2;
  - **C1 = p2fc − p2f** (fix (i) ON in both arms);
  - the whole stack = p2fc − s0.
- **Kept protects per frame:** take p2fc's `C1 keep-watch: N protects kept so far` lines. Divide the change in N across the window by the frames in the window. About 1.6 faults per frame means the ring case; about 17 means the game rewrites the whole buffer.
- **Upload KB/f: two untimed side runs.** #7 adds +1-3 ms/f to GPU Commands, so it never runs in a timing arm.
  - Run 1 is p2f and run 2 is p2fc. Both add `shared_memory_upload_hash_log=true` and `slow_frame_log_ms=1`, the same recipe as Agent 3's u-diag run. Each needs ≥ 220 s on the title with no input.
  - Parse each with `python bench/agent12/s4_uhash.py <run dir>` (default window 70-220 s).
  - Realised u = 1 − KB/f(p2fc) / KB/f(p2f). Compare it with u_block 0.934 (title, S4a; the C1 call in `perf-notes/agent5-uploads.md`).
  - Cross-check against the `cpu-write invalidations Nx K KB` field on the same slow-frame lines. At title on S4a it reads ~3848 KB/f against the hash log's 3844.
  - P2's counter is not a KB/f source. It counts full-buffer memexport fallbacks, which is gate 4.

## Expected effect

These are upper bounds, from `perf-notes/agent5-uploads.md` L980-987. The pairs of figures come from S4.2's slow-state profiles (a = devoff2, b = devoffB). At normal clocks, everything is ~3-4× smaller.

- **GPU Commands, C1 = p2fc − p2f:** up to **−3.40 / −3.59 ms/f** (u_block 0.934 × 3.64 / 3.85). With block widening it is −3.25 to −3.40 / −3.44 to −3.59, because 255-407 KB/f still re-uploads against 3844 today. At normal clocks that is roughly −0.85 to −1.2 ms/f.
- **Main:** the lock-time protects (0.54 / 1.02 ms/f) go away, and faults come back at 10-40 µs each.
  - At 1.59 faults per frame, Main saves 0.48-0.52 / 0.96-1.00 ms/f.
  - At 16.7 faults per frame, the net is between +0.37 and −0.13 / +0.85 and +0.35 ms/f (minus = a cost).
- **Fix (i)'s G hold (p2f − p2):** 0.003-0.17 ms/f. **P2 (p2 − s0):** small; there is no estimate here.

## Caveats

- u was measured on the title screen of S4a with no input. A level with figures may write more of the buffer per frame.
- An identical rewrite still faults under C1, so the realised u falls below u_block. Side run 2 and the kept count show how far.
- Window 4 was the first window after the 08:29 Windows Update (DTT/IPF extensions). Compare W6 within itself, not against window 3.
